import json
from typing import Dict, Any
import ollama
from fastapi import HTTPException, status
from core.config import settings


async def generate_test_from_content(
        material_title: str, content: str,
        num_questions: int = 5,
        pass_threshold: int = 70
):
    if not content or len(content.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Material content is too short to generate a test. Minimum 50 characters required."
        )

    system_prompt = """Ты - опытный преподаватель, создающий тесты для студентов.

Твоя задача: создать тест на основе учебного материала.

Требования:
1. Вопросы должны проверять понимание ключевых концепций
2. Используй разные типы вопросов
3. Варианты ответов должны быть правдоподобными
4. Добавь подсказки к вопросам
5. Все на русском языке

ВАЖНО: Верни ТОЛЬКО валидный JSON, без дополнительного текста!

Формат JSON:
{
  "title": "Название теста",
  "questions": [
    {
      "text": "Текст вопроса?",
      "type": "single",
      "hint_text": "Подсказка",
      "options": [
        {"content": "Вариант 1", "is_correct": false},
        {"content": "Вариант 2", "is_correct": true},
        {"content": "Вариант 3", "is_correct": false}
      ]
    }
  ]
}

Типы вопросов:
- single: один правильный ответ (3-4 варианта)
- multiple: несколько правильных ответов (4-5 вариантов)
- true_false: верно/неверно (варианты: "Верно", "Неверно")"""

    user_prompt = f"""Создай тест из {num_questions} вопросов.

Материал: {material_title}

Содержание:
{content[:3000]}

Создай разнообразный тест с вопросами разных типов."""

    try:
        try:
            ollama.list()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Ollama service is not available. Please make sure Ollama is running. Error: {str(e)}"
            )

        response = ollama.chat(
            model=settings.OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            format="json",
            options={
                "temperature": 0.7,
                "num_predict": 2000,
            }
        )

        result_text = response['message']['content']
        test_data = json.loads(result_text)
        if "questions" not in test_data or not test_data["questions"]:
            raise ValueError("AI did not generate questions")

        for idx, question in enumerate(test_data["questions"], start=1):
            question["position"] = idx
            q_type = question.get("type")
            if q_type not in ["single_choice", "multiple_choice", "true_false"]:
                question["type"] = "single_choice"

        test_data["num_questions"] = len(test_data["questions"])
        test_data["pass_threshold"] = pass_threshold

        return test_data

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse AI response as JSON: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )


def validate_generated_test(test_data: Dict[str, Any]) -> bool:
    if not isinstance(test_data, dict):
        return False

    if "questions" not in test_data:
        return False

    questions = test_data["questions"]
    if not isinstance(questions, list) or len(questions) == 0:
        return False

    for question in questions:
        if not isinstance(question, dict):
            return False

        required_fields = ["text", "type", "options"]
        if not all(field in question for field in required_fields):
            return False

        options = question["options"]
        if not isinstance(options, list) or len(options) < 2:
            return False

        has_correct = any(opt.get("is_correct", False) for opt in options)
        if not has_correct:
            return False

    return True


