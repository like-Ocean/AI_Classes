import httpx
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

from core.config import settings

async def test_timeweb_api():
    """Тестирование API Timeweb Cloud AI"""

    print("=" * 60)
    print("Testing Timeweb Cloud AI API")
    print("=" * 60)
    print(f"Base URL: {settings.TIMEWEB_FULL_BASE_URL}")
    print(f"Agent Access ID: {settings.TIMEWEB_AGENT_ACCESS_ID}")
    print(f"API Key: {'Set' if settings.TIMEWEB_API_KEY else 'Not set'}")
    print("=" * 60)

    # Подготовка заголовков
    headers = {
        "Content-Type": "application/json"
    }

    if settings.TIMEWEB_API_KEY:
        headers["Authorization"] = f"Bearer {settings.TIMEWEB_API_KEY}"

    # Тестовый запрос
    payload = {
        "model": "gpt-4",  # Будет проигнорирован агентом
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "Hello! Please respond with: 'API connection successful'"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }

    try:
        print("\n[1] Sending test request to /v1/chat/completions...")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print("-" * 60)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.TIMEWEB_FULL_BASE_URL}/v1/chat/completions",
                headers=headers,
                json=payload
            )

            print(f"\n[2] Response Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"[3] Response Body:")
                print(json.dumps(data, indent=2, ensure_ascii=False))

                # Извлекаем ответ AI
                if "choices" in data and len(data["choices"]) > 0:
                    ai_response = data["choices"][0]["message"]["content"]
                    print("\n" + "=" * 60)
                    print("✅ SUCCESS! AI Response:")
                    print("=" * 60)
                    print(ai_response)
                    print("=" * 60)
                else:
                    print("\n⚠️ WARNING: Response structure unexpected")

                return True
            else:
                print(f"[3] Error Response:")
                print(response.text)
                print("\n❌ FAILED: Non-200 status code")
                return False

    except httpx.TimeoutException:
        print("\n❌ FAILED: Request timeout")
        return False
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}: {str(e)}")
        return False


async def test_simple_call():
    """Тестирование простого /call endpoint"""

    print("\n" + "=" * 60)
    print("Testing Simple Call Endpoint")
    print("=" * 60)

    headers = {
        "Content-Type": "application/json"
    }

    if settings.TIMEWEB_API_KEY:
        headers["Authorization"] = f"Bearer {settings.TIMEWEB_API_KEY}"

    payload = {
        "message": "Hello! Can you hear me?",
        "parent_message_id": None
    }

    try:
        print(f"\n[1] Sending request to /call...")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print("-" * 60)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.TIMEWEB_FULL_BASE_URL}/call",
                headers=headers,
                json=payload
            )

            print(f"\n[2] Response Status: {response.status_code}")
            print(f"[3] Response Body:")
            print(response.text)

            if response.status_code == 200:
                print("\n✅ SUCCESS!")
                return True
            else:
                print("\n❌ FAILED")
                return False

    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}: {str(e)}")
        return False


async def test_models_endpoint():
    """Тестирование /v1/models endpoint"""

    print("\n" + "=" * 60)
    print("Testing Models Endpoint")
    print("=" * 60)

    headers = {}
    if settings.TIMEWEB_API_KEY:
        headers["Authorization"] = f"Bearer {settings.TIMEWEB_API_KEY}"

    try:
        print(f"\n[1] Sending request to /v1/models...")
        print("-" * 60)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{settings.TIMEWEB_FULL_BASE_URL}/v1/models",
                headers=headers
            )

            print(f"\n[2] Response Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"[3] Available Models:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                print("\n✅ SUCCESS!")
                return True
            else:
                print(f"[3] Error: {response.text}")
                print("\n❌ FAILED")
                return False

    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}: {str(e)}")
        return False


async def run_all_tests():
    """Запуск всех тестов"""

    print("\n" + "🚀" * 30)
    print("TIMEWEB CLOUD AI - API TESTS")
    print("🚀" * 30 + "\n")

    results = []

    # Test 1: Chat Completions
    result1 = await test_timeweb_api()
    results.append(("Chat Completions", result1))

    # Test 2: Simple Call
    result2 = await test_simple_call()
    results.append(("Simple Call", result2))

    # Test 3: Models
    result3 = await test_models_endpoint()
    results.append(("Models Endpoint", result3))

    # Итоги
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    print("=" * 60)

    total_passed = sum(1 for _, success in results if success)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    print("=" * 60)


if __name__ == "__main__":
    # Запуск тестов
    asyncio.run(run_all_tests())
