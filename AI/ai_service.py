import httpx
import json
from typing import Dict, Any, List
from core.config import settings
from .prompts import get_test_generation_prompt, get_simple_test_prompt


class AIService:
    def __init__(self):
        self.base_url = settings.TIMEWEB_FULL_BASE_URL
        self.api_key = settings.TIMEWEB_API_KEY
        self.headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    async def generate_test(
            self,
            material_content: str,
            num_questions: int = 5,
            question_types: List[str] = None
    ) -> Dict[str, Any]:
        if question_types is None:
            question_types = ["single", "multiple"]

        prompt = get_test_generation_prompt(
            material_content, num_questions, question_types
        )

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "Ты - эксперт по созданию образовательных тестов. "
                               "Генерируй тесты на русском языке в формате JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": settings.AI_TEMPERATURE,
            "max_tokens": settings.AI_MAX_TOKENS
        }

        try:
            async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=self.headers,
                    json=payload
                )

                if response.status_code != 200:
                    raise Exception(
                        f"API error {response.status_code}: {response.text}"
                    )

                data = response.json()
                content = data["choices"][0]["message"]["content"]

                test_data = self._parse_json_response(content)

                self._validate_test_structure(test_data, num_questions)

                return test_data

        except httpx.TimeoutException:
            raise Exception("AI request timeout")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in AI response: {str(e)}")
        except Exception as e:
            raise Exception(f"AI generation failed: {str(e)}")

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        content = content.strip()

        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        return json.loads(content)

    def _validate_test_structure(
            self, test_data: Dict[str, Any], expected_questions: int
    ):
        if "questions" not in test_data:
            raise ValueError("Missing 'questions' field in response")

        if not isinstance(test_data["questions"], list):
            raise ValueError("'questions' must be an array")

        questions = test_data["questions"]

        if len(questions) != expected_questions:
            raise ValueError(
                f"Expected {expected_questions} questions, got {len(questions)}"
            )

        for i, question in enumerate(questions, 1):
            required_fields = ["text", "type", "options"]
            for field in required_fields:
                if field not in question:
                    raise ValueError(
                        f"Question {i}: missing required field '{field}'"
                    )

            if question["type"] not in ["single", "multiple"]:
                raise ValueError(
                    f"Question {i}: invalid type '{question['type']}'"
                )

            options = question["options"]
            if not isinstance(options, list) or len(options) != 4:
                raise ValueError(
                    f"Question {i}: must have exactly 4 options"
                )

            correct_count = sum(1 for opt in options if opt.get("is_correct"))

            if question["type"] == "single" and correct_count != 1:
                raise ValueError(
                    f"Question {i}: single choice must have exactly 1 correct answer"
                )

            if question["type"] == "multiple" and correct_count < 2:
                raise ValueError(
                    f"Question {i}: multiple choice must have at least 2 correct answers"
                )

    async def test_connection(self) -> Dict[str, Any]:
        try:
            prompt = get_simple_test_prompt()

            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 100
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=self.headers,
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"]["message"]["content"]

                    return {
                        "status": "success",
                        "message": content,
                        "model": "deepseek-chat",
                        "base_url": self.base_url
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"API returned status {response.status_code}",
                        "details": response.text
                    }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }


ai_service = AIService()
