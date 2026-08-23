# ==============================================================================
# МОДУЛЬ ИНТЕРПРЕТАЦИИ ЗАПРОСОВ ЧЕРЕЗ GEMINI AI
# ==============================================================================
import json
import os
import google.generativeai as genai

# Инициализация Gemini API
API_KEY = os.environ.get("GEMINI_API_KEY", "")

SYSTEM_PROMPT = """
Ты — профессиональный AI-ассистент логиста ADY (Азербайджанские Железные Дороги).
Твоя задача — извлечь логистические параметры из текста запроса и вернуть STRICT JSON.

Правила извлечения:
1. Станции (from_station, to_station):
   - Если станция является погранпереходом/стыком или точкой входа/выхода из страны, укажи имя с постфиксом '-eksport' (например: 'Yalama-eksport', 'Böyük Kəsik-eksport').
   - Учитывай специфику Алята: 'Ələt', 'Ələt yeni', 'Ələt eksport Aktau', 'Ələt eksport Kurik', 'Ələt eksport-Türk.'. Если указан просто 'Алят-эксп', укажи 'Ələt-eksport'.
2. Страны (origin_country, destination_country):
   - Заполняй ТОЛЬКО если страна отправления или назначения явно упомянута в тексте. Если не указана — пиши null. НЕ выдумывай страны.
3. Порожний вагон (is_empty_wagon):
   - Если вагон порожний: gng_code = "99220000", wagon_axles = 4, fact_weight = 0.0 (если иное не указано пользователем).
4. Кругорейс (is_round_trip):
   - Ставь true, если есть упоминания: "с учетом порожнего возврата", "с возвратом", "обратно порожним", "кругорейс".
5. Собственный/приватный вагон (is_private_wagon):
   - По умолчанию true (СПС / приватный / собственный), если не указано инвентарный парки/вагон железной дороги.

Формат ответа (СТРОГО JSON):
{
  "from_station": "строка или null",
  "to_station": "строка или null",
  "origin_country": "строка или null",
  "destination_country": "строка или null",
  "gng_code": "строка или null",
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
    """
    Отправляет запрос в Gemini API, проверяет обязательные поля и возвращает словарь.
    Никаких угадаек: при ошибках выдает исключение с сообщением о причине.
    """
    if not API_KEY:
        raise ValueError(" Ошибка: Не задан API-ключ Gemini (GEMINI_API_KEY).")

    genai.configure(api_key=API_KEY)
    
    try:
        # Используем актуальную модель Gemini Flash
        model = genai.GenerativeModel("gemini-3.5-flash-lite")
        response = model.generate_content(
            f"{SYSTEM_PROMPT}\n\nЗапрос пользователя: {user_prompt}",
            generation_config={"response_mime_type": "application/json"}
        )
        parsed_data = json.loads(response.text)
    except Exception as e:
        raise ValueError(f" Ошибка обращения к Gemini API: {str(e)}")

    # Логика обработки порожнего вагона по умолчанию
    if parsed_data.get("is_empty_wagon"):
        if not parsed_data.get("gng_code"):
            parsed_data["gng_code"] = "99220000"
        if not parsed_data.get("wagon_axles"):
            parsed_data["wagon_axles"] = 4
        if parsed_data.get("fact_weight") is None:
            parsed_data["fact_weight"] = 0.0

    # Проверка обязательных полей
    missing_fields = []
    if not parsed_data.get("from_station"):
        missing_fields.append("Станция отправления (from_station)")
    if not parsed_data.get("to_station"):
        missing_fields.append("Станция назначения (to_station)")

    # Для груженого вагона проверяем ГНГ и вес
    if not parsed_data.get("is_empty_wagon"):
        if not parsed_data.get("gng_code"):
            missing_fields.append("Код ГНГ / YHN (gng_code)")
        if parsed_data.get("fact_weight") is None or parsed_data.get("fact_weight") <= 0:
            missing_fields.append("Фактический вес груза (fact_weight)")

    # Если обязательных данных не хватает — останавливаем процесс
    if missing_fields:
        missing_str = "\n- ".join(missing_fields)
        raise ValueError(f" Для расчета не хватает следующих обязательных данных:\n- {missing_str}")

    return parsed_data
