from AI import ai_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from models import Test, Question, AnswerOption, Material, User, Module
from models.Enums import QuestionType
from service.course_service import check_course_access


async def generate_test_with_ai(
        course_id: int, module_id: int,
        material_id: int, num_questions: int,
        question_types: List[str],
        pass_threshold: int, time_limit_minutes: int,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Material)
        .join(Module)
        .where(
            and_(
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found in this module"
        )

    material_content = ""
    if material.text_content:
        material_content = material.text_content
        print(material_content)
    elif material.transcript:
        material_content = material.transcript
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Material must have text_content or transcript for test generation"
        )

    try:
        ai_response = await ai_service.generate_test(
            material_content=material_content,
            num_questions=num_questions,
            question_types=question_types
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI generation failed: {str(e)}"
        )

    test = Test(
        title=ai_response.get("title", f"Тест по материалу: {material.title}"),
        num_questions=num_questions,
        time_limit_seconds=time_limit_minutes * 60 if time_limit_minutes else None,
        pass_threshold=pass_threshold,
        status="draft",
        generated_by_nn=True,
        created_by=user.id,
        module_id=module_id,
        material_id=material_id
    )

    db.add(test)
    await db.flush()

    for i, q_data in enumerate(ai_response.get("questions", []), 1):
        question = Question(
            test_id=test.id,
            text=q_data["text"],
            type=QuestionType(q_data["type"]),
            position=i,
            hint_text=q_data.get("hint_text")
        )

        db.add(question)
        await db.flush()

        for opt_data in q_data.get("options", []):
            option = AnswerOption(
                question_id=question.id,
                content=opt_data["content"],
                is_correct=opt_data["is_correct"]
            )
            db.add(option)

    await db.commit()
    await db.refresh(test)

    result = await db.execute(
        select(Test)
        .options(
            selectinload(Test.questions).selectinload(Question.options)
        )
        .where(Test.id == test.id)
    )
    test_loaded = result.scalar_one()

    return test_loaded
