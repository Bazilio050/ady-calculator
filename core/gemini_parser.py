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

def parse_user_request(user_prompt: str) -> dict:
    if not API_KEY:
        raise ValueError("Ошибка: Не задан API-ключ Gemini (GEMINI_API_KEY).")

    try:
        # Инициализация актуального клиента google-genai
        client = genai.Client(api_key=API_KEY)
        
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=f"Запрос пользователя: {user_prompt}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json"
            )
        )
        parsed_data = json.loads(response.text)
    except Exception as e:
        raise ValueError(f"Ошибка обращения к Gemini API: {str(e)}")

    # Автоподстановка для порожнего вагона
    if parsed_data.get("is_empty_wagon"):
        parsed_data["gng_code"] = "99220000"
        parsed_data["gng_name"] = "Порожний вагон"
        if not parsed_data.get("wagon_axles"):
            parsed_data["wagon_axles"] = 4
        if parsed_data.get("fact_weight") is None:
            parsed_data["fact_weight"] = 0.0

    # Жесткая проверка обязательных полей
    missing_fields = []
    if not parsed_data.get("from_station"):
        missing_fields.append("Станция отправления (from_station)")
    if not parsed_data.get("to_station"):
        missing_fields.append("Станция назначения (to_station)")

    # Проверка ГНГ и веса для груженого вагона
    if not parsed_data.get("is_empty_wagon"):
        if not parsed_data.get("gng_code"):
            missing_fields.append("Код ГНГ / YHN (укажите числовой код, например: 72, 4818)")
        if parsed_data.get("fact_weight") is None or parsed_data.get("fact_weight") <= 0:
            missing_fields.append("Фактический вес груза в тоннах (fact_weight)")

    if missing_fields:
        missing_str = "\n- ".join(missing_fields)
        raise ValueError(f"Для расчета не хватает следующих обязательных данных:\n- {missing_str}")

    return parsed_data
