from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from models import (
    TestAttempt, QuestionAttempt, Question, Test,
    TestAttemptFeedback, Material, AnswerOption
)
from AI.ai_service import ai_service


async def generate_feedback_for_attempt(
        test_attempt: TestAttempt, db: AsyncSession
) -> TestAttemptFeedback:
    print(f"🔍 Starting feedback generation for attempt_id={test_attempt.id}")

    result = await db.execute(
        select(TestAttempt)
        .options(
            selectinload(TestAttempt.test)
            .selectinload(Test.material),
            selectinload(TestAttempt.question_attempts)
            .selectinload(QuestionAttempt.question)
            .selectinload(Question.options)
        )
        .where(TestAttempt.id == test_attempt.id)
    )
    attempt = result.scalar_one()
    print(f"✅ Loaded attempt data")

    analysis = await _analyze_test_results_with_context(attempt, db)
    print(f"✅ Analysis done: score={analysis['score']}, passed={analysis['passed']}")

    try:
        print("🚀 Calling AI generate_feedback...")
        feedback_text = await ai_service.generate_feedback(
            material_title=analysis["material_title"],
            material_content=analysis["material_content"],
            score=analysis["score"],
            passed=analysis["passed"],
            total_questions=analysis["total_questions"],
            correct_count=analysis["correct_count"],
            incorrect_count=analysis["incorrect_count"],
            partial_correct_count=analysis["partial_correct_count"],
            incorrect_questions_with_answers=analysis["incorrect_questions_with_answers"]
        )
        print(f"✅ AI feedback generated ({len(feedback_text)} chars)")
    except Exception as e:
        print(f"❌ AI feedback failed: {e}")
        print(f"❌ Using fallback")
        feedback_text = _create_fallback_feedback(analysis)

    feedback = TestAttemptFeedback(
        test_attempt_id=attempt.id,
        feedback_text=feedback_text,
        generated_at=datetime.utcnow()
    )

    db.add(feedback)
    print("📝 Feedback object added to session")

    try:
        await db.commit()
        print("✅ DB commit successful")
    except Exception as commit_error:
        print(f"❌ DB commit failed: {commit_error}")
        await db.rollback()
        raise

    await db.refresh(feedback)
    print(f"✅ Feedback saved with id={feedback.id}")
    return feedback


async def _analyze_test_results_with_context(attempt: TestAttempt, db: AsyncSession) -> Dict[str, Any]:
    total_questions = len(attempt.question_attempts)
    correct_count = sum(1 for qa in attempt.question_attempts if qa.is_correct)

    material = attempt.test.material
    material_content = ""

    if material:
        if material.text_content:
            material_content += f"**Основной текст:**\n{material.text_content}\n\n"

        if material.transcript:
            material_content += f"**Расшифровка (транскрипт):**\n{material.transcript}\n\n"

        if not material_content:
            material_content = "Текст материала отсутствует"
    else:
        material_content = "Материал не найден"

    partial_correct_count = 0
    incorrect_questions_with_answers = []

    for qa in attempt.question_attempts:
        if qa.is_correct:
            continue

        partial_score = qa.answer.get("partial_score", 0.0) if qa.answer else 0.0

        if partial_score > 0:
            partial_correct_count += 1

        question = qa.question
        correct_options = [opt for opt in question.options if opt.is_correct]
        correct_answer_text = ", ".join([opt.content for opt in correct_options])

        student_answer_text = "Нет ответа"
        if qa.answer and "selected_option_ids" in qa.answer:
            selected_ids = qa.answer["selected_option_ids"]
            selected_options = [
                opt for opt in question.options
                if opt.id in selected_ids
            ]
            student_answer_text = ", ".join([opt.content for opt in selected_options])

        incorrect_questions_with_answers.append({
            "position": question.position,
            "text": question.text,
            "student_answer": student_answer_text,
            "correct_answer": correct_answer_text,
            "partial_score": partial_score,
            "hint_text": question.hint_text or "Нет подсказки"
        })

    incorrect_count = total_questions - correct_count

    return {
        "material_title": material.title if material else "Материал",
        "material_content": material_content,
        "score": attempt.score,
        "passed": attempt.passed,
        "total_questions": total_questions,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "partial_correct_count": partial_correct_count,
        "incorrect_questions_with_answers": incorrect_questions_with_answers
    }


def _create_fallback_feedback(analysis: Dict[str, Any]) -> str:
    score = analysis["score"]
    passed = analysis["passed"]
    correct_count = analysis["correct_count"]
    total_questions = analysis["total_questions"]
    material_title = analysis["material_title"]

    if passed:
        status = "Тест пройден"
        recommendation = (
            f"Повторите разделы материала «{material_title}», где были допущены ошибки, "
            f"чтобы закрепить знания."
        )
    else:
        status = "Тест не пройден"
        recommendation = (
            f"Рекомендуем внимательно изучить материал «{material_title}» заново "
            f"и пройти тест повторно."
        )

    fallback = f"""{status}

Результат: {score}% ({correct_count} из {total_questions} правильных ответов)

{recommendation}

Персонализированный анализ временно недоступен. Проконсультируйтесь с преподавателем для детального разбора ошибок."""

    return fallback
