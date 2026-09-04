# ==============================================================================
# МОДУЛЬ ИНТЕРПРЕТАЦИИ ЗАПРОСОВ ЧЕРЕЗ GEMINI AI (АКТУАЛЬНЫЙ GOOGLE-GENAI SDK)
# ==============================================================================
import json
import os
import time
import google.genai as genai
from google.genai import types

# ------------------------------------------------------------------------------
# БЛОК 1: Вспомогательная функция получения API-ключа
# ------------------------------------------------------------------------------
def get_api_key() -> str:
    """Универсальное извлечение API-ключа: из os.environ или из Streamlit Secrets"""
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
        
    return ""

# ------------------------------------------------------------------------------
# БЛОК 2: Полный системный промпт интерпретации естественного языка
# ------------------------------------------------------------------------------
SYSTEM_PROMPT = """
Ты — профессиональный AI-ассистент логиста ADY (Азербайджанские Железные Дороги).
Твоя задача — извлечь параметры из текста запроса и вернуть STRICT JSON.

Правила извлечения:
1. Код ГНГ / YHN (gng_code и gng_name):
   - Код ГНГ может быть числом от 2 до 8 цифр (например: '72', '2707', '3404', '4407', '48181', '8703', '99220000').
   - Находи Любое 2-8 значное число в тексте, обозначающее номенклатуру груза или его код (даже если оно стоит в начале, середине или рядом со словами 'цистерна', 'вагон', 'спс').
   - Записывай извлеченный числовой код STRICTLY как строку цифр в 'gng_code'.
   - ЕСЛИ В ТЕКСТЕ НЕТ ЧИСЛОВОГО КОДА ГНГ -> СТАВЬ null. НЕ ПОДБИРАЙ И НЕ УГАДЫВАЙ КОД.
   - В 'gng_name' возвращай краткое официальное название груза СТРОГО на языке интерфейса (AZ -> азербайджанский, RU -> русский, EN -> английский).

2. Станции (from_station, to_station):
   - Извлекай только чистые названия станций/стыков БЕЗ КОДОВ ЕСР И БЕЗ СКОБОК.
   - СТРОГО СОХРАНЯЙ ПОРЯДОК СТАНЦИЙ ИЗ ТЕКСТА: первая упомянутая станция/стык — это 'from_station', вторая — 'to_station'.
   - Если упоминается паром, 'ТРК', 'Туркменбаши', 'Актау', 'Курык' -> извлекай соответствующее имя станции ('ТРК', 'Ələt-eksp.Türk.', 'Актау', 'Курык').
   - Для погранпереходов возвращай латинские имена ADY (например: 'Yalama (eksport)', 'Böyük Kəsik (eksport)', 'Astara (eksport)', 'Culfa (eksport)').

3. Вес и норма загрузки (fact_weight):
   - Извлекай фактический вес груза в тоннах как число (например: 50т -> 50.0, 60.5 тонн -> 60.5).

4. Порожний вагон (is_empty_wagon):
   - Если в тексте есть слова 'порожний', 'boş', 'empty', 'возврат порожнего':
     gng_code = "99220000", wagon_axles = 4, fact_weight = 0.0, is_empty_wagon = true.
     Название груза в gng_name пиши на языке интерфейса ("Boş vaqon" для AZ, "Порожний вагон" для RU, "Empty wagon" для EN).

5. Флаги собственника и рейса:
   - Если в тексте ЕСТЬ слова 'СПС', 'спс', 'собственный', 'привлеченный', 'частный', 'xüsusi' -> "is_private_wagon": true.
   - Если в тексте ЕСТЬ слова 'МПС', 'мпс', 'инвентарный', 'государственный', 'парк жд', 'MPS' -> "is_private_wagon": false.
   - Если СПС/МПС ЯВНО НЕ УКАЗАНО -> по умолчанию "is_private_wagon": false.
   - is_round_trip: true, если есть фразы "с возвратом", "с учетом порожнего возврата", "кругорейс".

6. Вид перевозки (shipment_type):
   - Если погранпереходы находятся на границе и перевозка сквозная -> по умолчанию "shipment_type": "transit".
   - Если в тексте есть слово "импорт", "import", "idhal", "idxal" -> "shipment_type": "import".
   - Если в тексте есть слово "экспорт", "export", "ixrac" -> "shipment_type": "export".
   - Если в тексте есть слово "транзит", "transit", "tranzit" -> "shipment_type": "transit".

7. Тип вагона (wagon_type):
   - "tank" — цистерна, tank, çənd, бункер.
   - "autocar" — автомобилевоз, автовоз.
   - "two_tier_car_platform" — двухъярусная платформа.
   - "universal" — крытые, полувагоны, платформы, хопперы.
   - "arv" — автономный реф (АРВ / ARV).
   - "thermos" — вагон-термос / ледник.
   - "ref_section" — рефрижераторная секция.

8. Рефрижераторные секции и скидки:
   - ref_cars_count: количество грузовых вагонов в рефсекции (если есть).
   - apply_fresh_produce_discount: true, ТОЛЬКО если есть слова "фрукты", "овощи", "плодоовощные", "meyvə", "tərəvəz".
   - special_mark: "IZVK", "IZVT", "VTVK" или null.

Формат ответа (СТРОГО JSON):
{
  "from_station": "строка или null",
  "to_station": "строка или null",
  "origin_country": null,
  "destination_country": null,
  "gng_code": "строка с цифрами (от 2 до 8 знаков) или null",
  "gng_name": "строка или null",
  "fact_weight": число_или_null,
  "wagon_type": "universal/tank/arv/thermos/autocar/two_tier_car_platform/ref_section/passenger",
  "ref_cars_count": null,
  "apply_fresh_produce_discount": false,
  "special_mark": null,
  "shipment_type": "import/export/transit",
  "is_empty_wagon": false,
  "is_private_wagon": true/false,
  "is_round_trip": false,
  "wagon_axles": 4
}
"""

# ------------------------------------------------------------------------------
# БЛОК 3: Константы автоподстановки порожних вагонов
# ------------------------------------------------------------------------------
EMPTY_WAGON_NAMES = {
    "AZ": "Boş vaqon",
    "RU": "Порожний вагон",
    "EN": "Empty wagon",
}

# ------------------------------------------------------------------------------
# БЛОК 4: Основная функция парсинга через Gemini API (parse_user_request)
# ------------------------------------------------------------------------------
def parse_user_request(user_prompt: str, lang: str = "AZ") -> dict:
    """Отправляет текстовый запрос пользователя в Gemini API и возвращает распарсенный JSON."""
    api_key = get_api_key()
    if not api_key:
        raise ValueError("Ошибка: Не задан API-ключ Gemini (GEMINI_API_KEY).")

    parsed_data = {}
    max_retries = 3
    current_lang = (lang or "AZ").upper()
    
    for attempt in range(max_retries):
        try:
            client = genai.Client(api_key=api_key)
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
            break
        except Exception as e:
            err_msg = str(e)
            if ("503" in err_msg or "UNAVAILABLE" in err_msg or "overloaded" in err_msg) and attempt < max_retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            parsed_data = {"error": f"Ошибка обращения к Gemini API: {str(e)}"}

    if not isinstance(parsed_data, dict):
        parsed_data = {}

    parsed_data["lang"] = current_lang

    if parsed_data.get("is_empty_wagon"):
        parsed_data["gng_code"] = "99220000"
        parsed_data["gng_name"] = EMPTY_WAGON_NAMES.get(current_lang, "Boş vaqon")
        if not parsed_data.get("wagon_axles"):
            parsed_data["wagon_axles"] = 4
        if parsed_data.get("fact_weight") is None:
            parsed_data["fact_weight"] = 0.0

    return parsed_data
