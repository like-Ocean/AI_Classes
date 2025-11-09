def get_test_generation_prompt(
        material_content: str,
        num_questions: int,
        question_types: list[str]
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
