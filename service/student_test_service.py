from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import Dict, Any, List
from datetime import datetime, timedelta
from models import (
    Test, Question, TestAttempt, QuestionAttempt,
    Material, Module, CourseEnrollment, User
)
from models.Enums import QuestionType


# TODO: могут быть ошибки
def calculate_question_score(
        question: Question,
        selected_option_ids: List[int]
) -> tuple[bool, float]:
    """
    Вычисление баллов за вопрос с частичным оцениванием.

    Возвращает:
        (is_fully_correct, partial_score)
        - is_fully_correct: bool - полностью правильный ответ
        - partial_score: float - частичный балл от 0.0 до 1.0
    """
    if question.type == QuestionType.single:
        correct_ids = {opt.id for opt in question.options if opt.is_correct}
        selected_ids = set(selected_option_ids)
        is_correct = correct_ids == selected_ids
        return is_correct, 1.0 if is_correct else 0.0

    elif question.type == QuestionType.multiple:
        correct_ids = {opt.id for opt in question.options if opt.is_correct}
        selected_ids = set(selected_option_ids)

        if correct_ids == selected_ids:
            return True, 1.0

        correct_selected = len(correct_ids & selected_ids)
        incorrect_selected = len(selected_ids - correct_ids)
        total_correct = len(correct_ids)
        if total_correct == 0:
            return False, 0.0

        # Формула: (правильные выборы / всего правильных) - штраф за неправильные
        # Штраф = (неправильные / всего правильных) * 0.5 (половина штрафа)
        score = (correct_selected / total_correct) - (incorrect_selected / total_correct * 0.5)
        score = max(0.0, score)
        return False, score
    else:
        return False, 0.0


async def get_test_for_student(
        course_id: int, module_id: int,
        material_id: int, test_id: int,
        user: User, db: AsyncSession
):
    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            and_(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id == course_id
            )
        )
    )
    if not enrollment_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course"
        )

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
                Module.course_id == course_id,
                Test.status == "published"
            )
        )
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found or not published"
        )

    test.questions.sort(key=lambda q: q.position)

    questions_data = []
    for question in test.questions:
        options_data = [
            {"id": opt.id, "content": opt.content}
            for opt in question.options
        ]

        question_dict = {
            "id": question.id,
            "text": question.text,
            "type": question.type,
            "position": question.position,
            "hint_text": question.hint_text,
            "options": options_data
        }
        questions_data.append(question_dict)

    return {
        "id": test.id,
        "title": test.title,
        "num_questions": test.num_questions,
        "time_limit_seconds": test.time_limit_seconds,
        "pass_threshold": test.pass_threshold,
        "questions": questions_data
    }


async def start_test_attempt(
        course_id: int, module_id: int,
        material_id: int, test_id: int,
        user: User, db: AsyncSession
):
    test = await get_test_for_student(
        course_id, module_id,
        material_id, test_id, user, db
    )
    active_attempt_result = await db.execute(
        select(TestAttempt).where(
            and_(
                TestAttempt.test_id == test_id,
                TestAttempt.user_id == user.id,
                TestAttempt.finished_at.is_(None)
            )
        )
    )
    active_attempt = active_attempt_result.scalar_one_or_none()
    if active_attempt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have an active test attempt. Please finish it first."
        )
    blocked_attempt_result = await db.execute(
        select(TestAttempt).where(
            and_(
                TestAttempt.test_id == test_id,
                TestAttempt.user_id == user.id,
                TestAttempt.blocked_until.isnot(None),
                TestAttempt.blocked_until > datetime.utcnow()
            )
        )
    )
    blocked_attempt = blocked_attempt_result.scalar_one_or_none()
    if blocked_attempt:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are blocked from taking this test until {blocked_attempt.blocked_until}"
        )

    max_attempt_result = await db.execute(
        select(func.max(TestAttempt.attempt_number)).where(
            and_(
                TestAttempt.test_id == test_id,
                TestAttempt.user_id == user.id
            )
        )
    )
    max_attempt = max_attempt_result.scalar() or 0

    attempt = TestAttempt(
        test_id=test_id,
        user_id=user.id,
        attempt_number=max_attempt + 1
    )

    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)

    return attempt


async def submit_answer(
        course_id: int, module_id: int,
        material_id: int, test_id: int,
        attempt_id: int, question_id: int,
        answer_data: Dict[str, Any],
        hint_used: bool, user: User,
        db: AsyncSession
):
    result = await db.execute(
        select(TestAttempt)
        .options(selectinload(TestAttempt.test))
        .where(
            and_(
                TestAttempt.id == attempt_id,
                TestAttempt.test_id == test_id,
                TestAttempt.user_id == user.id
            )
        )
    )
    attempt = result.scalar_one_or_none()
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test attempt not found"
        )

    if attempt.finished_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test already finished"
        )

    question_result = await db.execute(
        select(Question)
        .options(selectinload(Question.options))
        .where(Question.id == question_id)
    )
    question = question_result.scalar_one_or_none()
    if not question or question.test_id != test_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found in this test"
        )

    existing_answer_result = await db.execute(
        select(QuestionAttempt).where(
            and_(
                QuestionAttempt.test_attempt_id == attempt_id,
                QuestionAttempt.question_id == question_id
            )
        )
    )
    existing_answer = existing_answer_result.scalar_one_or_none()
    if existing_answer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already answered this question"
        )

    is_fully_correct = False
    partial_score = 0.0
    if question.type in [QuestionType.single, QuestionType.multiple]:
        selected_ids = answer_data.get("selected_option_ids", [])
        is_fully_correct, partial_score = calculate_question_score(question, selected_ids)

    answer_data_with_score = answer_data.copy()
    answer_data_with_score["partial_score"] = partial_score

    question_attempt = QuestionAttempt(
        test_attempt_id=attempt_id,
        question_id=question_id,
        answer=answer_data_with_score,
        is_correct=is_fully_correct,
        hint_used=hint_used,
        attempt_number=1
    )

    db.add(question_attempt)

    attempt.current_question_id = question_id

    await db.commit()
    await db.refresh(question_attempt)

    return question_attempt


async def finish_test_attempt(
        course_id: int, module_id: int,
        material_id: int, test_id: int,
        attempt_id: int, user: User,
        db: AsyncSession
):
    result = await db.execute(
        select(TestAttempt)
        .options(
            selectinload(TestAttempt.test).selectinload(Test.questions),
            selectinload(TestAttempt.question_attempts)
        )
        .where(
            and_(
                TestAttempt.id == attempt_id,
                TestAttempt.test_id == test_id,
                TestAttempt.user_id == user.id
            )
        )
    )
    attempt = result.scalar_one_or_none()
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test attempt not found"
        )

    if attempt.finished_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test already finished"
        )

    total_questions = len(attempt.test.questions)
    answered_questions = len(attempt.question_attempts)
    if answered_questions < total_questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You must answer all questions. Answered: {answered_questions}/{total_questions}"
        )

    total_score = 0.0
    for qa in attempt.question_attempts:
        partial_score = qa.answer.get("partial_score", 1.0 if qa.is_correct else 0.0)
        total_score += partial_score

    score = round((total_score / total_questions * 100)) if total_questions > 0 else 0
    passed = score >= attempt.test.pass_threshold

    attempt.finished_at = datetime.utcnow()
    attempt.score = score
    attempt.passed = passed

    consecutive_fails = 0
    if not passed:
        previous_attempts_result = await db.execute(
            select(TestAttempt)
            .where(
                and_(
                    TestAttempt.test_id == test_id,
                    TestAttempt.user_id == user.id,
                    TestAttempt.id < attempt_id
                )
            )
            .order_by(TestAttempt.attempt_number.desc())
        )
        previous_attempts = list(previous_attempts_result.scalars().all())

        consecutive_fails = 1
        for prev_attempt in previous_attempts:
            if prev_attempt.attempt_number == attempt.attempt_number - consecutive_fails and not prev_attempt.passed:
                consecutive_fails += 1
            else:
                break

        if consecutive_fails >= 2:
            attempt.blocked_until = datetime.utcnow() + timedelta(minutes=5)

    await db.commit()
    await db.refresh(attempt)

    message = None
    if not passed:
        if consecutive_fails >= 2:
            message = "Test failed twice. You are blocked for 5 minutes. Please review the material."
        else:
            message = f"Test failed. You have {3 - consecutive_fails} attempt(s) left before being blocked."
    else:
        message = "Congratulations! Test passed successfully."

    response = {
        "id": attempt.id,
        "test_id": attempt.test_id,
        "user_id": attempt.user_id,
        "score": attempt.score,
        "passed": attempt.passed,
        "attempt_number": attempt.attempt_number,
        "started_at": attempt.started_at,
        "finished_at": attempt.finished_at,
        "blocked_until": attempt.blocked_until,
        "current_question_id": attempt.current_question_id,
        "blocked": attempt.blocked_until is not None,
        "consecutive_fails": consecutive_fails,
        "message": message
    }

    return response


async def get_test_result(attempt_id: int, user: User, db: AsyncSession):
    result = await db.execute(
        select(TestAttempt)
        .options(
            selectinload(TestAttempt.test).selectinload(Test.questions).selectinload(Question.options),
            selectinload(TestAttempt.question_attempts)
        )
        .where(
            and_(
                TestAttempt.id == attempt_id,
                TestAttempt.user_id == user.id
            )
        )
    )
    attempt = result.scalar_one_or_none()
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test attempt not found"
        )

    if attempt.finished_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test not finished yet"
        )

    answers_map = {qa.question_id: qa for qa in attempt.question_attempts}
    questions_results = []
    for question in attempt.test.questions:
        correct_option_ids = [opt.id for opt in question.options if opt.is_correct]
        student_answer = answers_map.get(question.id)

        partial_score = 0.0
        if student_answer and student_answer.answer:
            partial_score = student_answer.answer.get("partial_score", 0.0)

        question_result = {
            "question_id": question.id,
            "question_text": question.text,
            "student_answer": student_answer.answer if student_answer else None,
            "correct_option_ids": correct_option_ids,
            "is_correct": student_answer.is_correct if student_answer else False,
            "hint_used": student_answer.hint_used if student_answer else False,
            "partial_score": round(partial_score * 100)
        }
        questions_results.append(question_result)

    return {
        "attempt_id": attempt.id,
        "test_id": attempt.test_id,
        "test_title": attempt.test.title,
        "attempt_number": attempt.attempt_number,
        "started_at": attempt.started_at,
        "finished_at": attempt.finished_at,
        "total_questions": len(attempt.test.questions),
        "correct_answers": sum(1 for qa in attempt.question_attempts if qa.is_correct),
        "score": attempt.score,
        "passed": attempt.passed,
        "questions_results": questions_results
    }


async def get_my_test_attempts(
        course_id: int, module_id: int,
        material_id: int, test_id: int,
        user: User, db: AsyncSession
):
    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            and_(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id == course_id
            )
        )
    )
    if not enrollment_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course"
        )
    result = await db.execute(
        select(TestAttempt)
        .options(selectinload(TestAttempt.test))
        .where(
            and_(
                TestAttempt.test_id == test_id,
                TestAttempt.user_id == user.id
            )
        )
        .order_by(TestAttempt.started_at.desc())
    )
    attempts = result.scalars().all()

    attempts_data = []
    for attempt in attempts:
        attempt_dict = {
            "id": attempt.id,
            "test_id": attempt.test_id,
            "test_title": attempt.test.title,
            "attempt_number": attempt.attempt_number,
            "started_at": attempt.started_at,
            "finished_at": attempt.finished_at,
            "score": attempt.score,
            "passed": attempt.passed
        }
        attempts_data.append(attempt_dict)

    return attempts_data
