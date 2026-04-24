from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from models import TestAttempt, User


async def get_test_attempt_with_validation(
    attempt_id: int, test_id: int,
    user: User, db: AsyncSession,
    load_test: bool = False,
    load_questions: bool = False,
    load_answers: bool = False
) -> TestAttempt:
    query = select(TestAttempt)
    if load_test:
        if load_questions:
            from models import Test, Question
            query = query.options(
                selectinload(TestAttempt.test)
                .selectinload(Test.questions)
                .selectinload(Question.options)
            )
        else:
            query = query.options(selectinload(TestAttempt.test))

    if load_answers:
        query = query.options(selectinload(TestAttempt.question_attempts))

    query = query.where(
        and_(
            TestAttempt.id == attempt_id,
            TestAttempt.test_id == test_id,
            TestAttempt.user_id == user.id
        )
    )

    result = await db.execute(query)
    attempt = result.scalar_one_or_none()
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test attempt not found"
        )

    return attempt


async def validate_attempt_not_finished(attempt: TestAttempt) -> None:
    if attempt.finished_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test already finished"
        )


async def validate_attempt_finished(attempt: TestAttempt) -> None:
    if attempt.finished_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test not finished yet"
        )


async def get_test_attempt_by_id(
    attempt_id: int, user: User,
    db: AsyncSession, load_test: bool = False,
    load_questions: bool = False,
    load_answers: bool = False
) -> TestAttempt:
    query = select(TestAttempt)
    if load_test:
        if load_questions:
            from models import Test, Question
            query = query.options(
                selectinload(TestAttempt.test)
                .selectinload(Test.questions)
                .selectinload(Question.options)
            )
        else:
            query = query.options(selectinload(TestAttempt.test))

    if load_answers:
        query = query.options(selectinload(TestAttempt.question_attempts))

    query = query.where(
        and_(
            TestAttempt.id == attempt_id,
            TestAttempt.user_id == user.id
        )
    )

    result = await db.execute(query)
    attempt = result.scalar_one_or_none()

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test attempt not found"
        )

    return attempt
