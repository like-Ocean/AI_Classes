from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import Dict, Any, List
from helpers.test_helper_service import (
    get_test_attempt_with_validation, validate_attempt_not_finished
)
from models import (
    Question, TestAttempt, QuestionAttempt, User
)
from datetime import datetime, timedelta
from AI.feedback import generate_feedback_for_attempt
from .student_test_service import calculate_question_score


async def submit_test_with_feedback(
        course_id: int, module_id: int,
        material_id: int, test_id: int,
        attempt_id: int, answers: List[Dict[str, Any]],
        user: User, db: AsyncSession
) -> Dict[str, Any]:

    attempt = await get_test_attempt_with_validation(
        attempt_id, test_id, user, db,
        load_test=True, load_questions=True
    )
    await validate_attempt_not_finished(attempt)

    if len(answers) != len(attempt.test.questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected {len(attempt.test.questions)} answers, got {len(answers)}"
        )

    question_ids = {q.id for q in attempt.test.questions}
    answer_question_ids = {a["question_id"] for a in answers}

    if question_ids != answer_question_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some questions are missing or extra questions provided"
        )

    questions_map = {}
    for question in attempt.test.questions:
        result = await db.execute(
            select(Question)
            .options(selectinload(Question.options))
            .where(Question.id == question.id)
        )
        questions_map[question.id] = result.scalar_one()

    total_score = 0.0
    for answer_data in answers:
        question_id = answer_data["question_id"]
        question = questions_map[question_id]

        is_correct, partial_score = calculate_question_score(
            question,
            answer_data["answer"].get("selected_option_ids", [])
        )

        total_score += partial_score

        answer_with_score = answer_data["answer"].copy()
        answer_with_score["partial_score"] = partial_score

        question_attempt = QuestionAttempt(
            test_attempt_id=attempt_id,
            question_id=question_id,
            answer=answer_with_score,
            is_correct=is_correct,
            hint_used=answer_data.get("hint_used", False),
            attempt_number=1
        )
        db.add(question_attempt)

    total_questions = len(attempt.test.questions)
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

    feedback_text = None
    try:
        feedback = await generate_feedback_for_attempt(attempt, db)
        feedback_text = feedback.feedback_text
    except Exception as e:
        print(f"Feedback generation failed: {e}")

    message = None
    if not passed:
        if consecutive_fails >= 2:
            message = "Test failed twice. You are blocked for 5 minutes. Please review the material."
        else:
            message = f"Test failed. You have {3 - consecutive_fails} attempt(s) left before being blocked."
    else:
        message = "Test completed successfully"

    return {
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
        "feedback_text": feedback_text,
        "message": message
    }
