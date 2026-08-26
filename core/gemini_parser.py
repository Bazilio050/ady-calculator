# ==============================================================================
# МОДУЛЬ ИЗВЛЕЧЕНИЯ ПАРАМЕТРОВ ИЗ ЗАПРОСА (GEMINI AI PARSER)
# ==============================================================================
import json
import logging
import os
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Считываем API-ключ Gemini из переменных окружения
API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Системный промпт с предметной областью ADY и зафиксированными правилами извлечения
SYSTEM_PROMPT = """
Ты — специализированный NLU-парсер железнодорожной логистики и тарифной системы ЗАО «Азербайджанские Железные Дороги» (ADY / АЖД).
Твоя единственная роль — анализировать текстовые запросы пользователей по железнодорожным грузоперевозкам, извлекать транспортные параметры и возвращать СТРОГО JSON-объект.

Предметная область:
- Железнодорожные станции и пограничные переходы Азербайджана, Грузии, России, Казахстана, Ирана и Турции.
- Подвижной состав (вагоны, платформы, цистерны, хопперы, контейнеры).
- Грузовые коды (ГНГ / ТН ВЭД) и параметры грузов (вес в тоннах, оси, длина вагонов, принадлежность СПС).
- Режимы перевозок (транзит, импорт, экспорт, внутренние перевозки).

### 1. ПРАВИЛА ИЗВЛЕЧЕНИЯ И НОРМАЛИЗАЦИИ СТАНЦИЙ (from_station, to_station):
- Исправляй опечатки пользователя и переводи названия станций в БАЗОВУЮ латиницу ADY:
  * "ялама", "ялам" -> "Yalama"
  * "беюк кясик", "бейук кясик", "бек кясик" -> "Böyük Kəsik"
  * "имишли", "имишлы" -> "İmişli"
  * "апшерон", "абшерон" -> "Abşeron"
  * "сальяны", "салян" -> "Salyan"
  * "баку" -> "Bakı yük"
  * "гянджа" -> "Gəncə"
  * "астара" -> "Astara"
  * "алят", "алет" -> "Ələt"
  * "алят новый", "yeni alat" -> "Ələt yeni"

- ФИКСАЦИЯ СУБ-ТЕРМИНАЛОВ И ФЛАГОВ ДЛЯ СТАНЦИИ АЛЯТ (в поля alat_terminal и is_exp_flag):
  * Если в тексте есть "курык", "крык" -> alat_terminal: "Kurik", is_exp_flag: true
  * Если в тексте есть "актау" -> alat_terminal: "Aktau", is_exp_flag: true
  * Если в тексте есть "трк", "туркменбаши" -> alat_terminal: "Turk", is_exp_flag: true
  * Если в тексте написано просто "алят экс", "алят эксп", "alat eksp" -> alat_terminal: null, is_exp_flag: true
  * Если обычная станция Алят без экспортного контекста -> alat_terminal: null, is_exp_flag: false

- СТРОГО ЗАПРЕЩЕНО генерировать 6-значные коды ЕСР (цифры) или приписки "-эксп.". Это делает Python!

### 2. ПРАВИЛА ОПРЕДЕЛЕНИЯ ТИПА ПЕРЕВОЗКИ (shipment_type):
- "tranzit": если явно написано "транзит" ИЛИ если в запросе указаны ДВЕ пограничные станции (например, Yalama и Böyük Kəsik, или Yalama и Ələt).
- "ixrac" (export): если явно написано "экспорт" или отправка из внутренней станции за границу.
- "idxal" (import): если явно написано "импорт" или въезд из-за границы на внутреннюю станцию.
- "daxili" (local): если перевозка между двумя внутренними стациями Азербайджана.

### 3. ПАРАМЕТРЫ ГРУЗА И ВАГОНОВ (если в тексте параметра нет — возвращай null):
- gng_code: строка (код ГНГ от 2 до 8 цифр) или null
- gng_name: краткое наименование груза или null
- fact_weight: масса груза в тоннах (число) или null
- wagon_type: "universal", "tank", "ref", "autocar", "passenger", "hopper", "platform" или null
- is_empty_wagon: true, если вагон порожний, иначе false
- is_private_wagon: true по умолчанию (собственный/СПС/арендованный), false если инвентарный
- is_round_trip: true, если указан кругорейс/возврат, иначе false
- wagon_axles: количество осей (число, по умолчанию 4)
- wagon_length: строка (длина вагона/платформы: "15m", "19.7m", "24m", "40ft", "80ft") или null
- origin_country: ISO-код страны отправления ("RU", "AZ", "KZ", "GE", "TR") или null
- destination_country: ISO-код страны назначения ("GE", "TR", "AZ", "RU", "KZ", "EU") или null
- final_destination_type: "georgia_local" (доставка под выгрузку в Грузию) | "georgia_transit" (транзит через порты/стыки Грузии) | null
- port_or_border: строка ("Poti", "Batumi", "Kartsakhi") или null

Формат ответа (СТРОГО JSON):
{
  "from_station": "строка или null",
  "to_station": "строка или null",
  "alat_terminal": "Kurik/Aktau/Turk или null",
  "is_exp_flag": true/false,
  "shipment_type": "tranzit/ixrac/idxal/daxili",
  "origin_country": "строка или null",
  "destination_country": "строка или null",
  "gng_code": "строка или null",
  "gng_name": "строка или null",
  "fact_weight": число_или_null,
  "wagon_type": "строка или null",
  "is_empty_wagon": true/false,
  "is_private_wagon": true/false,
  "is_round_trip": true/false,
  "wagon_axles": число,
  "wagon_length": "строка или null",
  "final_destination_type": "georgia_local/georgia_transit или null",
  "port_or_border": "строка или null"
}
"""

def parse_user_request(user_prompt: str, lang: str = "AZ") -> dict:
    """
    Основная функция NLU-парсинга запроса через Gemini 3.5 Flash-Lite.
    Принимает текст запроса пользователя и язык интерфейса.
    """
    if not API_KEY:
        raise ValueError("Ошибка: Не задан API-ключ Gemini (GEMINI_API_KEY).")

    # Формируем карту языков для вывода поля gng_name
    lang_map = {
        "AZ": "Azərbaycan dilində",
        "RU": "русском языке",
        "EN": "English language"
    }
    target_lang = lang_map.get(str(lang).upper(), "азербайджанском (Azerbaijani)")

    # Подготавливаем итоговый промпт с динамическим требованием языка
    prompt_with_lang = (
        f"{SYSTEM_PROMPT}\n\n"
        f"ТРЕБОВАНИЕ ПО ЯЗЫКУ: Верни значение поля 'gng_name' строго на {target_lang} языке!\n\n"
        f"Запрос пользователя: {user_prompt}"
    )

    try:
        # Инициализируем клиента Gemini GenAI
        client = genai.Client(api_key=API_KEY)
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt_with_lang,
            config=types.GenerateContentConfig(
                temperature=0.0, # Нулевая температура для максимальной точности
                response_mime_type="application/json"
            )
        )
        parsed_data = json.loads(response.text)
    except Exception as e:
        logger.error(f"Ошибка обращения к Gemini API: {str(e)}")
        raise ValueError(f"Ошибка обращения к Gemini API: {str(e)}")

    # Логика обработки порожнего вагона (перенесена из твоей исходной логики)
    if parsed_data.get("is_empty_wagon"):
        parsed_data["gng_code"] = "99220000"
        empty_names = {"AZ": "Boş vaqon", "RU": "Порожний вагон", "EN": "Empty wagon"}
        parsed_data["gng_name"] = empty_names.get(str(lang).upper(), "Boş vaqon")
        if not parsed_data.get("wagon_axles"):
            parsed_data["wagon_axles"] = 4
        if parsed_data.get("fact_weight") is None:
            parsed_data["fact_weight"] = 0.0

    return parsed_data
