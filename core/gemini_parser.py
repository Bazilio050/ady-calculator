import os
import json
import re
import time
from google import genai
from google.genai import types

def parse_user_request(user_prompt: str, lang: str = "AZ") -> dict:
    """
    Разбирает запрос пользователя и ВСЕГДА возвращает словарь (dict).
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        try:
            import streamlit as st
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass

    if not api_key:
        return {"error": "GEMINI_API_KEY не найден в переменных окружения или Secrets."}

    client = genai.Client(api_key=api_key)

    system_instruction = """
    Ты — эксперт по железнодорожной логистике ADY (Азербайджанские железные дороги).
    Твоя задача — извлечь параметры перевозки из текста и вернуть ТОЛЬКО JSON без каких-либо дополнительных комментариев или тегов ```json.

    КРИТИЧЕСКИ ВАЖНОЕ ПРАВИЛО ДЛЯ СТАНЦИЙ:
    Названия станций (from_station и to_station) ВСЕГДА пиши в официальном формате ADY на латинице (например: "Yalama", "Böyük Kəsik", "Abşeron", "Astara", "İmişli", "Ələt eksport", "Salyan", "Gəncə", "Bakı yük").
    Даже если пользователь ввел "Ялама", "Алят эксп" или "Апшерон", в JSON возвращай строго "Yalama", "Ələt eksport" и "Abşeron".

    Схема вывода JSON:
    {
        "from_station": "Официальное название станции на латинице ADY",
        "to_station": "Официальное название станции на латинице ADY",
        "gng_code": "4-6 значный код ГНГ/GNG (строка или null)",
        "fact_weight": 35.0,
        "wagon_type": "covered",
        "shipment_type": "import",
        "is_empty_wagon": false,
        "is_private_wagon": true,
        "is_round_trip": false,
        "wagon_axles": 4,
        "manual_distance_km": null
    }
    """
    
    try:
        max_retries = 3
    response = None

    for attempt in range(max_retries):
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
            if response and response.text:
                break
        except Exception as e:
            if ("503" in str(e) or "UNAVAILABLE" in str(e)) and attempt < max_retries - 1:
                time.sleep(1)
                continue
            else:
                raise e

        # Защита: проверяем, что распарсенный результат — это словарь
        if not isinstance(parsed_data, dict):
            return {"error": f"Gemini вернул не словарь, а {type(parsed_data).__name__}"}

        return {
            "raw_input": user_prompt,  # <-- ДОБАВЛЕНО: сохраняем исходный текст ввода!
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

    except Exception as e:
        # Гарантируем возврат словаря с ключом error
        return {"error": f"Ошибка Gemini API: {str(e)}"}
