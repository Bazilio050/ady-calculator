import os
import json
import re
from google import genai
from google.genai import types

def parse_user_request(user_prompt: str, lang: str = "AZ") -> dict:
    """
    Разбирает текстовый или голосовой запрос пользователя с помощью Gemini API
    и возвращает структурированный словарь параметров для расчета тарифа.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        # Проверяем наличие ключа в streamlit secrets, если доступен
        try:
            import streamlit as st
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass

    if not api_key:
        raise ValueError("GEMINI_API_KEY не найден в переменных окружения или secrets.")

    client = genai.Client(api_key=api_key)

    system_instruction = """
    Ты — эксперт по железнодорожной логистике ADY (Азербайджанские железные дороги).
    Твоя задача — извлечь параметры перевозки из текста пользователя и вернуть ТОЛЬКО JSON без каких-либо дополнительных комментариев или тегов ```json.

    Схема вывода JSON:
    {
        "from_station": "Название станции отправления (например, Yalama)",
        "to_station": "Название станции назначения (например, Böyük Kəsik)",
        "gng_code": "6-значный код ГНГ/GNG или первые 2-4 цифры, если указаны (строка или null)",
        "fact_weight": "фактический вес в тоннах (число float, по умолчанию 0.0)",
        "wagon_type": "тип вагона ('covered'/'universal'/'flat'/'tank'/'grain'/'refrigerated')",
        "shipment_type": "вид перевозки ('import'/'export'/'transit'/'local')",
        "is_empty_wagon": false,
        "is_private_wagon": true,
        "is_round_trip": false,
        "wagon_axles": 4,
        "manual_distance_km": null
    }
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1,
                response_mime_type="application/json"
            )
        )

        raw_text = response.text.strip()
        # Очистка от случайных Markdown-тегов
        raw_text = re.sub(r"^```json\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)

        parsed_data = json.loads(raw_text)

        # Приведение типов и значения по умолчанию
        return {
            "from_station": parsed_data.get("from_station", ""),
            "to_station": parsed_data.get("to_station", ""),
            "gng_code": str(parsed_data.get("gng_code")) if parsed_data.get("gng_code") else None,
            "fact_weight": float(parsed_data.get("fact_weight", 0.0) or 0.0),
            "wagon_type": parsed_data.get("wagon_type", "universal"),
            "shipment_type": parsed_data.get("shipment_type", "import"),
            "is_empty_wagon": bool(parsed_data.get("is_empty_wagon", False)),
            "is_private_wagon": bool(parsed_data.get("is_private_wagon", True)),
            "is_round_trip": bool(parsed_data.get("is_round_trip", False)),
            "wagon_axles": int(parsed_data.get("wagon_axles", 4) or 4),
            "manual_distance_km": float(parsed_data.get("manual_distance_km")) if parsed_data.get("manual_distance_km") else None
        }

    except json.JSONDecodeError:
        raise ValueError("Ошибка обработки ответа Gemini: получен невалидный JSON.")
    except Exception as e:
        raise ValueError(f"Ошибка при обращении к Gemini API: {str(e)}")
