from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from models import Test, Question, AnswerOption, Material, User, Module
from models.Enums import QuestionType
from schemas.tests import (
    TestCreateRequest, TestUpdateRequest,
    QuestionCreateRequest, QuestionUpdateRequest,
    AnswerOptionCreate, AnswerOptionUpdate
)
from service.course_service import check_course_access


# TODO: Тесты создаются, нужно добавить возможность пользователею проходить тесты.
#  генерацию тестов через нейронку на основе материала после которого идеёт тест

# TESTS
async def create_test(
        course_id: int, module_id: int,
        material_id: int,
        data: TestCreateRequest,
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

    test = Test(
        title=data.title,
        num_questions=data.num_questions,
        time_limit_seconds=data.time_limit_seconds,
        pass_threshold=data.pass_threshold,
        status=data.status,
        generated_by_nn=False,
        created_by=user.id,
        module_id=module_id,
        material_id=material_id
    )

    db.add(test)
    await db.commit()
    await db.refresh(test)

    return test


async def get_test_detail(
        course_id: int, module_id: int,
        material_id: int, test_id: int,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Test)
        .options(
            selectinload(Test.questions).selectinload(Question.options)
        )
        .join(Material)
        .join(Module)
        .where(
            and_(
                Test.id == test_id,
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )

    test.questions.sort(key=lambda q: q.position)

    return test


async def update_test(
        course_id: int, module_id: int,
        material_id: int, test_id: int,
        data: TestUpdateRequest,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Test)
        .join(Material)
        .join(Module)
        .where(
            and_(
                Test.id == test_id,
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )

    if data.title is not None:
        test.title = data.title
    if data.num_questions is not None:
        test.num_questions = data.num_questions
    if data.time_limit_seconds is not None:
        test.time_limit_seconds = data.time_limit_seconds
    if data.pass_threshold is not None:
        test.pass_threshold = data.pass_threshold
    if data.status is not None:
        if data.status not in ["draft", "published"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status must be 'draft' or 'published'"
            )
        test.status = data.status

    await db.commit()
    await db.refresh(test)

    return test


async def delete_test(
        course_id: int, module_id: int,
        material_id: int, test_id: int,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Test)
        .join(Material)
        .join(Module)
        .where(
            and_(
                Test.id == test_id,
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )

    await db.delete(test)
    await db.commit()


# QUESTIONS

async def create_question(
        course_id: int, module_id: int,
        material_id: int, test_id: int,
        data: QuestionCreateRequest,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Test)
        .join(Material)
        .join(Module)
        .where(
            and_(
                Test.id == test_id,
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )

    if data.type in [QuestionType.single, QuestionType.multiple]:
        if not data.options or len(data.options) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question type '{data.type}' requires at least 2 options"
            )
        correct_count = sum(1 for opt in data.options if opt.is_correct)
        if data.type == QuestionType.single and correct_count != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Single choice question must have exactly 1 correct answer"
            )
        if data.type == QuestionType.multiple and correct_count < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Multiple choice question must have at least 1 correct answer"
            )

    question = Question(
        test_id=test_id,
        text=data.text,
        type=data.type,
        position=data.position,
        hint_text=data.hint_text
    )

    db.add(question)
    await db.flush()

    if data.options:
        for option_data in data.options:
            option = AnswerOption(
                question_id=question.id,
                content=option_data.content,
                is_correct=option_data.is_correct
            )
            db.add(option)

    await db.commit()
    await db.refresh(question)

    result = await db.execute(
        select(Question)
        .options(selectinload(Question.options))
        .where(Question.id == question.id)
    )
    question_with_options = result.scalar_one()

    return question_with_options


async def update_question(
        course_id: int, module_id: int,
        material_id: int, test_id: int,
        question_id: int,
        data: QuestionUpdateRequest,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Question)
        .options(selectinload(Question.options))
        .join(Test)
        .join(Material)
        .join(Module)
        .where(
            and_(
                Question.id == question_id,
                Test.id == test_id,
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    if data.type is not None and data.type == QuestionType.single:
        correct_count = sum(1 for opt in question.options if opt.is_correct)
        if correct_count > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change to single_choice: question has {correct_count} "
                       "correct answers. Single choice questions must have exactly 1 correct answer."
            )
        if correct_count == 0 and question.options:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change to single_choice: question has no correct answers. "
                       "Single choice questions must have exactly 1 correct answer."
            )

    if data.text is not None:
        question.text = data.text
    if data.type is not None:
        question.type = data.type
    if data.position is not None:
        question.position = data.position
    if data.hint_text is not None:
        question.hint_text = data.hint_text

    await db.commit()
    await db.refresh(question)

    return question


async def delete_question(
        course_id: int, module_id: int,
        material_id: int, test_id: int,
        question_id: int, user: User,
        db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Question)
        .join(Test)
        .join(Material)
        .join(Module)
        .where(
            and_(
                Question.id == question_id,
                Test.id == test_id,
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    await db.delete(question)
    await db.commit()


# ANSWER

async def add_answer_option(
        course_id: int, module_id: int,
        material_id: int, test_id: int,
        question_id: int, data: AnswerOptionCreate,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Question)
        .options(selectinload(Question.options))
        .join(Test)
        .join(Material)
        .join(Module)
        .where(
            and_(
                Question.id == question_id,
                Test.id == test_id,
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    if question.type == QuestionType.single and data.is_correct:
        existing_correct = any(opt.is_correct for opt in question.options)
        if existing_correct:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Single choice question can have only one correct answer. "
                       "Please mark the existing correct answer as incorrect first."
            )

    option = AnswerOption(
        question_id=question_id,
        content=data.content,
        is_correct=data.is_correct
    )

    db.add(option)
    await db.commit()
    await db.refresh(option)

    return option


async def update_answer_option(
        course_id: int, module_id: int,
        material_id: int, test_id: int,
        question_id: int, option_id: int,
        data: AnswerOptionUpdate,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(AnswerOption)
        .options(
            selectinload(AnswerOption.question).selectinload(Question.options)
        )
        .join(Question)
        .join(Test)
        .join(Material)
        .join(Module)
        .where(
            and_(
                AnswerOption.id == option_id,
                Question.id == question_id,
                Test.id == test_id,
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    option = result.scalar_one_or_none()
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer option not found"
        )
    if data.is_correct is not None and data.is_correct and \
            option.question.type == QuestionType.single:
        other_correct = any(
            opt.is_correct and opt.id != option_id
            for opt in option.question.options
        )
        if other_correct:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Single choice question can have only one correct answer. "
                       "Please mark the existing correct answer as incorrect first."
            )

    if data.content is not None:
        option.content = data.content
    if data.is_correct is not None:
        option.is_correct = data.is_correct

    await db.commit()
    await db.refresh(option)

    return option


async def delete_answer_option(
        course_id: int, module_id: int,
        material_id: int, test_id: int,
        question_id: int, option_id: int,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(AnswerOption)
        .join(Question)
        .join(Test)
        .join(Material)
        .join(Module)
        .where(
            and_(
                AnswerOption.id == option_id,
                Question.id == question_id,
                Test.id == test_id,
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    option = result.scalar_one_or_none()
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer option not found"
        )

    await db.delete(option)
    await db.commit()
