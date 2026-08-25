# ==============================================================================
# МОДУЛЬ ИНТЕРПРЕТАЦИИ ЗАПРОСОВ ЧЕРЕЗ GEMINI AI (АКТУАЛЬНЫЙ GOOGLE-GENAI SDK)
# ==============================================================================
import json
import os
import google.genai as genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY", "")

SYSTEM_PROMPT = """
Ты — профессиональный AI-ассистент логиста ADY (Азербайджанские Железные Дороги).
Твоя задача — извлечь параметры из текста запроса и вернуть STRICT JSON.

Правила извлечения:
1. Код ГНГ / YHN (gng_code) и Наименование (gng_name):
   - ПРИОРИТЕТ: Ищи в тексте любое числовое значение кода ГНГ (любой длины от 2 до 8 цифр, например: '72', '1001', '31024', '48182000'). 
   - Если в тексте есть цифры кода — ты ЖЕСТКО ОБЯЗАН записать их в 'gng_code'!
   - Для найденного кода напиши его официальное наименование в 'gng_name' (2-4 слова max).
2. Станции (from_station, to_station):
   - Извлекай название станций СТРОГО на азербайджанской латинице без использования кириллических букв (например: 'Sumqayıt', 'Yalama', 'Biləcəri', 'Abşeron').
   - Добавляй 6-значный код ЕСР, если знаешь: 'Yalama (547508)', 'Sumqayıt (546305)', 'Abşeron (548004)', 'Biləcəri (546808)'.
   - Для Алята и морских портов передавай контекст: 'Ələt', 'Ələt yeni', 'Ələt eksport Aktau', 'Ələt eksport Kurik', 'Ələt eksport-Türk.'.
   - Если упоминаются Курык / Курыт -> пиши 'Ələt eksport Kurik'. Если Актау -> 'Ələt eksport Aktau'. Если ТРК / Туркменистан / Туркменбаши -> 'Ələt eksport-Türk.'.

3. Страны (origin_country, destination_country):
   - Заполняй ТОЛЬКО если страна явным образом указана в тексте. Если нет — пиши null.

4. Порожний вагон (is_empty_wagon):
   - Если вагон порожний: gng_code = "99220000", wagon_axles = 4, fact_weight = 0.0, gng_name = "Boş vaqon".

5. Флаги:
   - is_round_trip: true, если есть фразы "с возвратом", "с учетом порожнего возврата", "кругорейс".
   - is_private_wagon: true по умолчанию (СПС), если не указано МПС/инвентарный.

Формат ответа (СТРОГО JSON):
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
            model="gemini-3.7-flash",
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
