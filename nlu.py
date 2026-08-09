import os
import json
from google import genai
from google.genai import types
from utils import normalize_st_name

# ==============================================================================
# СИСТЕМНЫЙ ПРОМПТ ДЛЯ GEMINI NLU
# ==============================================================================
GEMINI_SYSTEM_INSTRUCTION = """
Ты — специализированный NLU-парсер железнодорожного тарифного калькулятора Азербайджанских железных дорог (ADY).
Твоя задача — извлечь параметры перевозки из текста пользователя и вернуть СТРОГО валидный JSON.

---

### 1. ПРАВИЛА НОРМАЛИЗАЦИИ СТАНЦИЙ
Приводи названия станций СТРОГО к следующим каНОНИЧЕСКИМ КЛЮЧАМ:

* **Баку / Баку-Товарная:**
  - "баку-тов", "баку тов", "баку товарная", "bakı-tov", "bakı yük", "баку", "bakı", "baki" -> **"Bakı-Yük"**
* **Бакинский Порт:**
  - "баку порт", "баку торговый порт", "bakı ticarət limanı", "bakı liman" -> **"Bakı Ticarət Limanı"**
* **Алят и Морские Паромы (Курык / Актау / Туркменбаши):**
  - "алят", "ələt", "elet", "курык", "kurik", "актау", "aktau", "туркменбаши", "turkmenbashi", "алят экспорт курык", "алят экспорт актау" -> **"Ələt"**
  - "алят ени", "ələt yeni" -> **"Ələt-Yeni"**
* **Прочие специфические станции ADY:**
  - "астара", "astara", "astara eks" -> **"Astara"**
  - "мингечевир шехер", "mingəçevir şəhər", "mingəçevir" -> **"Mingəçevir-Şəhər"**
  - "карадаг", "qaradağ", "карадаг терминал" -> **"Qaradağ"**
  - "гушчу корпю", "quşçu körpü" -> **"Quşçu Körpü"**
  - "сангачал", "сангачал тер", "sanqaçal" -> **"Sanqaçal"**
  - "союг булаг", "soyuqbulaq", "soyuq-bulaq" -> **"Soyuqbulaq"**
  - "з. тагиев", "з.тагиев", "z.tağıyev" -> **"Z.Tağıyev"**
  - "з.тагиев сортировочная", "z.tağıyev çeşidləmə" -> **"Z.Tağıyev-Çeşidləmə"**
  - "забрат 2", "zabrat 2", "zabrat ii" -> **"Zabrat-II"**
  - "ялама", "yalama" -> **"Yalama"**
  - "беюк кесик", "böyük kəsik", "boyuk kesik" -> **"Böyük Kəsik"**

---

### 2. ПРАВИЛА ПАРСИНГА ОСТАЛЬНЫХ ПАРАМЕТРОВ

1. **Маршрут (route_from / route_to):**
   - Если указана только одна станция и второе направление — Ялама, Беюк-Кесик или Астара, подставляй соответствующую пограничную станцию.

2. **Код ГНГ / Груз (cargo_gng_code / cargo_name):**
   - Извлекай 4-значный или 8-значный код ГНГ (например: "3404", "2710", "29051100").
   - Если передано название груза, определяй подходящий код ГНГ.

3. **Вес (actual_weight_tons):**
   - Числовое значение веса в тоннах (float). Например: 55.0.

4. **Тип вагона (wagon_type):**
   - "cistern" (цистерна, çən, бункер)
   - "universal" (крытый, полувагон, платформа)
   - "refrigerated" (рефрижератор, ИЗО, термос, секция)

5. **Парк вагона (park_type):**
   - "SPS" (собственный / частный / əlavə / özəl) — по умолчанию.
   - "MPS" (инвентарный парк / железная дорога).

6. **Явный режим (explicit_mode):**
   - "import", "export", "transit" или null.

---

### 3. СТРУКТУРА ВЫХОДНОГО JSON

Верни ответ СТРОГО в следующем формате без markdown-тегов:

{
  "route_from": "Bakı-Yük",
  "route_to": "Yalama",
  "cargo_gng_code": "3404",
  "cargo_name": "Neft məhsulları",
  "actual_weight_tons": 55.0,
  "wagon_type": "cistern",
  "park_type": "SPS",
  "explicit_mode": null,
  "requested_period": null
}
"""


def parse_user_input_with_gemini(user_input: str, api_key: str = None, *args, **kwargs) -> dict:
    """
    Отправляет текстовый запрос пользователя в Gemini NLU через новый SDK google-genai.
    """
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY не найден в переменных окружения.")

    client = genai.Client(api_key=api_key)
    
    # Жестко зафиксированная модель по твоему требованию
    model_name = "gemini-3.5-flash-lite"

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.1,
        system_instruction=GEMINI_SYSTEM_INSTRUCTION
    )

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=user_input,
            config=config
        )
        return json.loads(response.text.strip())

    except Exception as e:
        print(f"Ошибка Gemini NLU ({model_name}): {e}")
        return {
            "route_from": "Bakı-Yük",
            "route_to": "Yalama",
            "cargo_gng_code": "",
            "cargo_name": "",
            "actual_weight_tons": 60.0,
            "wagon_type": "universal",
            "park_type": "SPS",
            "explicit_mode": None,
            "requested_period": None
        }


def validate_nlu_input(parsed_data: dict) -> dict:
    """
    Валидирует и нормализует извлеченные данные перед передачей в расчетный движок engine.py.
    """
    if not isinstance(parsed_data, dict):
        parsed_data = {}

    parsed_data["route_from"] = normalize_st_name(parsed_data.get("route_from", "Bakı-Yük"))
    parsed_data["route_to"] = normalize_st_name(parsed_data.get("route_to", "Yalama"))

    try:
        parsed_data["actual_weight_tons"] = float(parsed_data.get("actual_weight_tons") or 60.0)
    except (ValueError, TypeError):
        parsed_data["actual_weight_tons"] = 60.0

    if not parsed_data.get("wagon_type"):
        parsed_data["wagon_type"] = "universal"

    if not parsed_data.get("park_type"):
        parsed_data["park_type"] = "SPS"

    return parsed_data


def call_gemini_nlu(user_input: str, api_key: str = None, *args, **kwargs) -> dict:
    """
    Главная внешняя функция, поддерживающая гибкое количество аргументов от app.py.
    """
    if not api_key and args:
        api_key = args[0]

    raw_parsed_data = parse_user_input_with_gemini(user_input, api_key, *args, **kwargs)
    return validate_nlu_input(raw_parsed_data)
