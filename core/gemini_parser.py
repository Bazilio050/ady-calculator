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

    SYSTEM_PROMPT = """
Ты — профессиональный AI-ассистент логиста ADY (Азербайджанские Железные Дороги).
Твоя задача — извлечь параметры из текста запроса и вернуть STRICT JSON.

Правила извлечения:
1. Код ГНГ / YHN (gng_code):
   - Ищи В ИСКЛЮЧИТЕЛЬНОМ ПОРЯДКЕ числовой код ГНГ (например: '72', '4818', '2713').
   - ЕСЛИ В ТЕКСТЕ НЕТ ЧИСЛОВОГО КОДА ГНГ -> СТАВЬ null. НЕ ПОДБИРАЙ И НЕ УГАДЫВАЙ КОД.
   - Если код ГНГ указан в виде числа, верни его и добавь краткое официальное наименование груза в 'gng_name' (2-3 слова max).

2. Станции (from_station, to_station):
   - Извлекай только чистые названия станций/стыков БЕЗ КОДОВ ЕСР И БЕЗ СКОБОК.
   - Для погранпереходов возвращай латинские имена ADY (например: 'Yalama (eksport)', 'Böyük Kəsik (eksport)', 'Astara (eksport)', 'Culfa (eksport)').
   - ДЛЯ СТАНЦИИ АЛЯТ (ƏLƏT):
     * Если написано просто "Алят", "Алят экс", "Алят эксп", "Ələt eksp" (БЕЗ слов Актау, Курык, Туркменбаши, ТРК) -> возвращай строго: 'Ələt eksport'.
     * Возвращай конкретные порты ТОЛЬКО при наличии явных слов в тексте:
       - 'Ələt eksport Aktau' — только если есть слово "Актау" или "Aktau".
       - 'Ələt eksport Kurik' — только если есть слово "Курык" или "Kuryk".
       - 'Ələt eksport-Türk.' — только если есть слово "Туркменбаши", "Турк" или "ТРК".

3. Страны (origin_country, destination_country):
   - Заполняй ТОЛЬКО если страна явным образом указана в тексте. Если нет — пиши null.

4. Порожний вагон (is_empty_wagon):
   - Если вагон порожний: gng_code = "99220000", wagon_axles = 4, fact_weight = 0.0, gng_name = "Порожний вагон".

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
                return {"error": f"Ошибка Gemini API: {str(e)}"}

    if not response or not response.text:
        return {"error": "Не удалось получить ответ от Gemini API."}

    try:
        raw_text = response.text.strip()
        raw_text = re.sub(r"^```json\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)

        parsed_data = json.loads(raw_text)

        # Защита: проверяем, что распарсенный результат — это словарь
        if not isinstance(parsed_data, dict):
            return {"error": f"Gemini вернул не словарь, а {type(parsed_data).__name__}"}

        return {
            "raw_input": user_prompt,
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
        return {"error": f"Ошибка обработки ответа Gemini: {str(e)}"}
