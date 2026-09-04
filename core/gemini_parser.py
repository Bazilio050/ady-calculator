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
# БЛОК 2: Системный промпт интерпретации естественного языка (SYSTEM_PROMPT)
# ------------------------------------------------------------------------------
SYSTEM_PROMPT = """
Ты — профессиональный AI-ассистент логиста ADY (Азербайджанские Железные Дороги).
Твоя задача — извлечь параметры из текста запроса и вернуть STRICT JSON.

Правила извлечения:
1. Код ГНГ / YHN (gng_code и gng_name):
   - Ищи В ИСКЛЮЧИТЕЛЬНОМ ПОРЯДКЕ числовой код ГНГ (например: '72', '1001', '4407', '48181', '8703').
   - ЕСЛИ В ТЕКСТЕ НЕТ ЧИСЛОВОГО КОДА ГНГ -> СТАВЬ null. НЕ ПОДБИРАЙ И НЕ УГАДЫВАЙ КОД.
   - Числовой код ГНГ ВСЕГДА извлекай отдельно в 'gng_code', независимо от опечаток в названиях станций.
   - В 'gng_name' возвращай краткое официальное название груза СТРОГО на том языке, который указан в "Текущий язык интерфейса" (AZ -> азербайджанский, RU -> русский, EN -> английский).

2. Станции (from_station, to_station):
   - Извлекай только чистые названия станций/стыков БЕЗ КОДОВ ЕСР И БЕЗ СКОБОК.
   - Исправляй опечатки в названиях станций (например: "Ялмма" -> "Yalama (eksport)", "Беук" -> "Böyük Kəsik", "БК" -> "Böyük Kəsik").
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
   - Если в тексте ЕСТЬ слова "СПС", "собственный", "привлеченный", "частный", "xüsusi" -> "is_private_wagon": true.
   - Если в тексте ЕСТЬ слова "МПС", "инвентарный", "государственный", "парк жд", "MPS" -> "is_private_wagon": false.
   - Если СПС/МПС ЯВНО НЕ УКАЗАНО в тексте -> ПО УМОЛЧАНИЮ "is_private_wagon": false (считать как МПС).

6. Вид перевозки (shipment_type):
   - Если погранпереходы находятся на границе (например, с Яламы на БК или наоборот) и перевозка сквозная -> по умолчанию "shipment_type": "transit".
   - Если в тексте есть слово "импорт", "import", "idhal", "idxal" -> возвращай "shipment_type": "import".
   - Если в тексте есть слово "экспорт", "export", "ixrac" -> возвращай "shipment_type": "export".
   - Если в тексте есть слово "транзит", "transit", "tranzit" -> возвращай "shipment_type": "transit".

7. Тип вагона (wagon_type) - СТРОГИЕ ПРАВИЛА РАЗГРАНИЧЕНИЯ:
   - "autocar" — СТАВЬ ВСЕГДА, если написано "автомобилевоз", "автовоз", "avtomobildaşıyan", ЕСЛИ НЕТ слов "двухъярусный", "2-ярусный", "ikimərtəbəli".
   - "two_tier_car_platform" — СТАВЬ ТОЛЬКО И ИСКЛЮЧИТЕЛЬНО при наличии слов "двухъярусный", "2-ярусный", "двухэтажный", "ikimərtəbəli".
   - "universal" — крытые, полувагоны, платформы.
   - "tank" — цистерны.
   - "arv" — автономные рефрижераторные вагоны (АРВ / ARV / автономный реф).
   - "thermos" — вагон-термос / вагон-ледник / ИВ / ВТ.
   - "ref_section" — рефрижераторная секция (РС / рефсекция).

8. Рефрижераторные секции, скидки и отметки (СЕКЦИИ И СПЕЦИАЛЬНЫЕ ФЛАГИ):
   - ref_cars_count: Извлекай количество грузовых вагонов в рефсекции.
     * Если написаны схемы типа "5+1", "1+5", "5 вагонов", "секция 5" -> ставь ref_cars_count: 5.
     * Если "3+1", "1+3" -> ставь ref_cars_count: 3.
     * Если "2+1", "1+2" -> ставь ref_cars_count: 2.
     * Если "1+1" -> ставь ref_cars_count: 1.
     * Если указана рефсекция без количества -> по умолчанию ставь ref_cars_count: 4 (или null).
   - apply_fresh_produce_discount: true, ТОЛЬКО если в тексте явным образом есть слова "фрукты", "овощи", "плодоовощные", "meyvə", "tərəvəz" или коды ГНГ 04100-04400, 05100-05300. В остальных случаях: false.
   - special_mark: Возвращай строку "IZVK", "IZVT", "VTVK" или null, если эти отметки явно присутствуют в тексте.

Формат ответа (СТРОГО JSON):
{
  "from_station": "строка или null",
  "to_station": "строка или null",
  "origin_country": "строка или null",
  "destination_country": "строка или null",
  "gng_code": "строка или null",
  "gng_name": "строка или null",
  "fact_weight": число_или_null,
  "wagon_type": "universal/tank/arv/thermos/autocar/two_tier_car_platform/ref_section/passenger",
  "ref_cars_count": число_или_null,
  "apply_fresh_produce_discount": true/false,
  "special_mark": "IZVK/IZVT/VTVK/null",
  "shipment_type": "import/export/transit",
  "is_empty_wagon": true/false,
  "is_private_wagon": true/false,
  "is_round_trip": true/false,
  "wagon_axles": число
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
                model="gemini-3.6-flash",
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
