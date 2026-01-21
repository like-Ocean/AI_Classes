import json


def get_test_generation_prompt(
        material_content: str, num_questions: int, question_types: list[str]
):
    max_content_length = 8000
    if len(material_content) > max_content_length:
        material_content = material_content[:max_content_length] + "..."

    types_description = []
    if "single" in question_types:
        types_description.append('"single" - один правильный ответ')
    if "multiple" in question_types:
        types_description.append('"multiple" - несколько правильных ответов (2-3)')

    types_str = ", ".join(types_description)

    prompt = f"""На основе следующего учебного материала составь тест из {num_questions} вопросов.

**УЧЕБНЫЙ МАТЕРИАЛ:**
{material_content}

**ТРЕБОВАНИЯ К ТЕСТУ:**
1. Создай ровно {num_questions} вопросов
2. Типы вопросов: {types_str}
3. Каждый вопрос должен иметь ровно 4 варианта ответа
4. Сложность вопросов: лёгкие (30%), средние (50%), сложные (20%)
5. Вопросы должны проверять понимание материала, а не просто запоминание
6. Все варианты ответов должны быть правдоподобными

**ВАЖНО: Формат ответа**
Отвечай ТОЛЬКО валидным JSON. Никакого дополнительного текста до или после JSON.

{{
  "title": "Краткое название теста (макс 100 символов)",
  "questions": [
    {{
      "text": "Чёткий, конкретный текст вопроса",
      "type": "single",
      "hint_text": "Полезная подсказка (или null)",
      "options": [
        {{"content": "Первый вариант ответа", "is_correct": true}},
        {{"content": "Второй вариант ответа", "is_correct": false}},
        {{"content": "Третий вариант ответа", "is_correct": false}},
        {{"content": "Четвёртый вариант ответа", "is_correct": false}}
      ]
    }},
    {{
      "text": "Текст другого вопроса",
      "type": "multiple",
      "hint_text": null,
      "options": [
        {{"content": "Первый вариант", "is_correct": true}},
        {{"content": "Второй вариант", "is_correct": true}},
        {{"content": "Третий вариант", "is_correct": false}},
        {{"content": "Четвёртый вариант", "is_correct": false}}
      ]
    }}
  ]
}}

**ПРАВИЛА ВАЛИДАЦИИ:**
- Для типа "single": РОВНО 1 вариант с is_correct = true
- Для типа "multiple": 2-3 варианта с is_correct = true
- Все вопросы должны быть связаны с материалом
- Не используй варианты типа "Все вышеперечисленное" или "Ничего из перечисленного"
- Вопросы и ответы должны быть на русском языке

Сгенерируй тест в формате JSON. Верни ТОЛЬКО JSON, больше ничего."""

    return prompt


def get_simple_test_prompt():
    return """Ответь на русском языке одним предложением: "Соединение с AI успешно установлено"

Верни ответ в JSON формате:
{
  "status": "success",
  "message": "Соединение с AI успешно установлено"
}
"""


def get_feedback_prompt(
        material_title: str,
        material_content: str,
        score: int, passed: bool,
        total_questions: int, correct_count: int,
        incorrect_count: int, partial_correct_count: int,
        incorrect_questions_with_answers: list[dict]
) -> str:

    max_content_length = 6500
    if len(material_content) > max_content_length:
        material_content = material_content[:max_content_length] + "..."

    incorrect_summary = []
    for q in incorrect_questions_with_answers:
        incorrect_summary.append({
            "position": q["position"],
            "question_text": q["text"],
            "student_answer": q.get("student_answer", "Нет ответа"),
            "correct_answer": q["correct_answer"],
            "partial_score": q["partial_score"],
            "explanation": q.get("hint_text", "Нет объяснения")
        })

    prompt = f"""Ты - опытный преподаватель, который анализирует результаты теста студента и даёт персонализированный фидбек.

**КОНТЕКСТ: УЧЕБНЫЙ МАТЕРИАЛ**
Название: {material_title}

Содержание материала:
{material_content}

---

**РЕЗУЛЬТАТЫ СТУДЕНТА:**
- Итоговый балл: {score}% ({correct_count} из {total_questions} правильных ответов)
- Статус: {"✅ ТЕСТ ПРОЙДЕН" if passed else "❌ ТЕСТ НЕ ПРОЙДЕН"}
- Полностью правильных: {correct_count}
- Частично правильных: {partial_correct_count}
- Неправильных: {incorrect_count}

**ДЕТАЛЬНЫЙ АНАЛИЗ ОШИБОК:**
{json.dumps(incorrect_summary, ensure_ascii=False, indent=2)}

---

**ЗАДАЧА:**
На основе учебного материала и результатов теста напиши мотивирующий персонализированный фидбек студенту (250-350 слов).

**СТРУКТУРА ФИДБЕКА:**

1. **Вступление (2-3 предложения)**
   - Поздравь/поддержи в зависимости от результата
   - Общая оценка уровня освоения материала

2. **Анализ сильных сторон (2-3 предложения)**
   - Какие темы/концепции студент освоил хорошо
   - Что получилось лучше всего
   - На что можно опираться дальше

3. **Конкретные рекомендации по ошибкам (самая важная часть, 4-5 предложений)**
   - Для КАЖДОГО вопроса с ошибкой:
     * Объясни, почему ответ неверный
     * Укажи, какую КОНКРЕТНУЮ тему/раздел из материала нужно повторить
     * Дай краткое пояснение правильного ответа в контексте материала
   - Используй фразы типа:
     * "В вопросе #X ты ошибся с темой [название], которая рассматривается в разделе [раздел материала]..."
     * "Обрати внимание на материал о [тема] - там объясняется, что..."
     * "Рекомендую вернуться к части материала про [тема] и перечитать..."

4. **Мотивация и план действий (2-3 предложения)**
   - Что сделать дальше (повторить материал, пройти тест снова, и т.д.)
   - Мотивирующее завершение

**ВАЖНЫЕ ТРЕБОВАНИЯ:**
- Пиши простым, дружелюбным языком (на "ты")
- Используй эмодзи умеренно (2-3 на весь текст)
- Ссылайся на КОНКРЕТНЫЕ части учебного материала
- НЕ дублируй текст из материала целиком, только краткие отсылки
- Фокус на ПРАКТИЧЕСКИХ рекомендациях, а не общих фразах
- Тональность: конструктивная, мотивирующая, но профессиональная

**ФОРМАТ ОТВЕТА:**
Верни ТОЛЬКО текст фидбека, без JSON, без заголовков, без markdown разметки (можно использовать ** для выделения).
Начинай сразу с текста фидбека."""

    return prompt
