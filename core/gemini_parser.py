# ==============================================================================
# МОДУЛЬ ИНТЕРПРЕТАЦИИ ЗАПРОСОВ ЧЕРЕЗ GEMINI AI (АКТУАЛЬНЫЙ GOOGLE-GENAI SDK)
# ==============================================================================
import json
import os
import time
import google.genai as genai
from google.genai import types

def get_api_key() -> str:
    """Универсальное извлечение API-ключа: из os.environ или из Streamlit Secrets"""
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
        
    return ""

SYSTEM_PROMPT = """
Ты — профессиональный AI-ассистент логиста ADY (Азербайджанские Железные Дороги).
Твоя задача — извлечь параметры из текста запроса и вернуть STRICT JSON.

Правила извлечения:
1. Код ГНГ / YHN (gng_code и gng_name):
   - Ищи В ИСКЛЮЧИТЕЛЬНОМ ПОРЯДКЕ числовой код ГНГ (например: '72', '1001', '4407', '48181').
   - ЕСЛИ В ТЕКСТЕ НЕТ ЧИСЛОВОГО КОДА ГНГ -> СТАВЬ null. НЕ ПОДБИРАЙ И НЕ УГАДЫВАЙ КОД.
   - Числовой код ГНГ ВСЕГДА извлекай отдельно в 'gng_code', независимо от опечаток в названиях станций.
   - В 'gng_name' возвращай краткое официальное название груза СТРОГО на том языке, который указан в "Текущий язык интерфейса" (AZ -> азербайджанский, RU -> русский, EN -> английский).

2. Станции (from_station, to_station):
   - Извлекай только чистые названия станций/стыков БЕЗ КОДОВ ЕСР И БЕЗ СКОБОК.
   - Исправляй опечатки в названиях станций (например: "Ялмма" -> "Yalama (eksport)", "Беук" -> "Böyük Kəsik").
   - Для погранпереходов возвращай латинские имена ADY (например: 'Yalama (eksport)', 'Böyük Kəsik (eksport)', 'Astara (eksport)', 'Culfa (eksport)').
   - ДЛЯ СТАНЦИИ АЛЯТ (ƏLƏT):
     * Если написано просто "Алят", "Alat", "Alet" (БЕЗ слов "эксп", "екс", "порт", "Актау", "Курык", "Туркменбаши", "ТРК") -> возвращай строго: 'Ələt'.
     * Если написано "Алят экс", "Алят эксп", "Ələt eksp", "Ələt eksport" -> возвращай строго: 'Ələt eksport'.
     * Возвращай конкретные порты ТОЛЬКО при наличии явных слов в тексте:
       - 'Ələt eksport Aktau' — только если есть слово "Актау" или "Aktau".
       - 'Ələt eksport Kurik' — только если есть слово "Курык" или "Kuryk".
       - 'Ələt eksport-Türk.' — только если есть слово "Туркменбаши", "Турк" или "ТРК".

3. Страны (origin_country, destination_country):
   - Заполняй ТОЛЬКО если страна явным образом указана в тексте. Если нет — пиши null.

4. Порожний вагон (is_empty_wagon):
   - Если вагон порожний: gng_code = "99220000", wagon_axles = 4, fact_weight = 0.0. Название груза в gng_name пиши на языке интерфейса ("Boş vaqon" для AZ, "Порожний вагон" для RU, "Empty wagon" для EN).

5. Флаги:
   - is_round_trip: true, если есть фразы "с возвратом", "с учетом порожнего возврата", "кругорейс".
   - is_private_wagon: true по умолчанию (СПС), если не указано МПС/инвентарный.

6. Вид перевозки (shipment_type):
   - Если в тексте есть слово "импорт", "import", "idhal", "idxal" -> возвращай "shipment_type": "import".
   - Если в тексте есть слово "экспорт", "export", "ixrac" -> возвращай "shipment_type": "export".
   - Если в тексте есть слово "транзит", "transit", "tranzit" -> возвращай "shipment_type": "transit".

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

EMPTY_WAGON_NAMES = {
    "AZ": "Boş vaqon",
    "RU": "Порожний вагон",
    "EN": "Empty wagon",
}

def parse_user_request(user_prompt: str, lang: str = "AZ") -> dict:
    api_key = get_api_key()
    if not api_key:
        raise ValueError("Ошибка: Не задан API-ключ Gemini (GEMINI_API_KEY).")

    parsed_data = {}
    max_retries = 3
    current_lang = (lang or "AZ").upper()
    
    # 1. Цикл с авто-повтором (Retry) для устранения ошибок 503 UNAVAILABLE
    for attempt in range(max_retries):
        try:
            client = genai.Client(api_key=api_key)
            
            # Передаем выбранный язык интерфейса прямо в запрос
            contents_text = f"Текущий язык интерфейса: {current_lang}\nЗапрос пользователя: {user_prompt}"

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=contents_text,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    max_output_tokens=500,
                )
            )
            parsed_data = json.loads(response.text)
            break  # Успешный ответ — выходим из цикла retry
        except Exception as e:
            err_msg = str(e)
            if ("503" in err_msg or "UNAVAILABLE" in err_msg or "overloaded" in err_msg) and attempt < max_retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            parsed_data = {"error": f"Ошибка обращения к Gemini API: {str(e)}"}

    if not isinstance(parsed_data, dict):
        parsed_data = {}

    # Сохраняем язык
    parsed_data["lang"] = current_lang

    # 2. Автоподстановка для порожнего вагона с учетом языка
    if parsed_data.get("is_empty_wagon"):
        parsed_data["gng_code"] = "99220000"
        parsed_data["gng_name"] = EMPTY_WAGON_NAMES.get(current_lang, "Boş vaqon")
        if not parsed_data.get("wagon_axles"):
            parsed_data["wagon_axles"] = 4
        if parsed_data.get("fact_weight") is None:
            parsed_data["fact_weight"] = 0.0

    return parsed_data
