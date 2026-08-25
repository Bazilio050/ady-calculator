# ==============================================================================
# МОДУЛЬ ИЗВЛЕЧЕНИЯ ПАРАМЕТРОВ ИЗ ЗАПРОСА (GEMINI AI PARSER)
# ==============================================================================
import json
import os
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Минималистичный промпт: запрещаем генерацию кодов ЕСР и скобок для станций
SYSTEM_PROMPT = """
Ты — AI-парсер логистических запросов ADY.
Твоя задача — извлечь из текста параметры и вернуть STRICT JSON.

Правила:
1. Станции (from_station, to_station):
   - Извлекай ТОЛЬКО сырые названия станций так, как они указаны или подразумеваются (например: "ялама", "сумгаит", "баладжары", "алят").
   - СТРОГО ЗАПРЕЩЕНО генерировать 6-значные коды ЕСР, цифры или скобки в названии станций.

2. Код ГНГ (gng_code) и наименование (gng_name):
   - Извлекай код ГНГ/ГНГ (от 2 до 8 цифр), если он указан.
   - Указывай краткое наименование груза.

3. Флаги и параметры:
   - fact_weight: масса груза в тоннах (число или null).
   - wagon_type: universal/tank/ref/autocar/passenger.
   - is_empty_wagon: true, если вагон порожний.
   - is_private_wagon: true по умолчанию (собственный/арендованный).
   - is_round_trip: true, если указан кругорейс / возврат.
   - wagon_axles: количество осей (по умолчанию 4).

Формат ответа (JSON):
{
  "from_station": "строка или null",
  "to_station": "строка или null",
  "origin_country": "строка или null",
  "destination_country": "строка или null",
  "gng_code": "строка или null",
  "gng_name": "строка или null",
  "fact_weight": число_или_null,
  "wagon_type": "universal/tank/ref/autocar/passenger",
  "shipment_type": "import/export/transit",
  "is_empty_wagon": true/false,
  "is_private_wagon": true/false,
  "is_round_trip": true/false,
  "wagon_axles": число
}
"""

def parse_user_request(user_prompt: str, lang: str = "AZ") -> dict:
    if not API_KEY:
        raise ValueError("Ошибка: Не задан API-ключ Gemini (GEMINI_API_KEY).")

    lang_map = {
        "AZ": "Azərbaycan dilində",
        "RU": "русском языке",
        "EN": "English language"
    }
    target_lang = lang_map.get(str(lang).upper(), "азербайджанском (Azerbaijani)")

    prompt_with_lang = (
        f"{SYSTEM_PROMPT}\n\n"
        f"ТРЕБОВАНИЕ ПО ЯЗЫКУ: Верни значение поля 'gng_name' строго на {target_lang} языке!\n\n"
        f"Запрос пользователя: {user_prompt}"
    )

    try:
        client = genai.Client(api_key=API_KEY)
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt_with_lang,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        parsed_data = json.loads(response.text)
    except Exception as e:
        raise ValueError(f"Ошибка обращения к Gemini API: {str(e)}")

    if parsed_data.get("is_empty_wagon"):
        parsed_data["gng_code"] = "99220000"
        empty_names = {"AZ": "Boş vaqon", "RU": "Порожний вагон", "EN": "Empty wagon"}
        parsed_data["gng_name"] = empty_names.get(str(lang).upper(), "Boş vaqon")
        if not parsed_data.get("wagon_axles"):
            parsed_data["wagon_axles"] = 4
        if parsed_data.get("fact_weight") is None:
            parsed_data["fact_weight"] = 0.0

    return parsed_data
