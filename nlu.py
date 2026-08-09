import os
import json
import re
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
Приводи названия станций СТРОГО к следующим КАНАНИЧЕСКИМ КЛЮЧАМ:

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
   - "import", "export", "transit" или "transit".

---

### 3. СТРУКТУРА ВЫХОДНОГО JSON

Верни ответ СТРОГО в следующем формате:

{
  "route_from": "Bakı-Yük",
  "route_to": "Yalama",
  "cargo_gng_code": "2710",
  "cargo_name": "Neft məhsulları",
  "actual_weight_tons": 55.0,
  "wagon_type": "cistern",
  "park_type": "SPS",
  "explicit_mode": "transit",
  "requested_period": "2026-08"
}
"""


def _get_valid_api_key(api_key: str = None, *args) -> str:
    """Извлекает корректный API ключ, фильтруя языковые аргументы вроде 'az' или 'ru'."""
    candidate_keys = [api_key] + list(args)
    for key in candidate_keys:
        if key and isinstance(key, str) and len(key) > 15 and not key.lower() in ["az", "ru", "en"]:
            return key
    return os.getenv("GEMINI_API_KEY", "")


def parse_user_input_with_gemini(user_input: str, api_key: str = None, *args, **kwargs) -> dict:
    """
    Отправляет текстовый запрос пользователя в Gemini NLU через SDK google-genai.
    """
    final_api_key = _get_valid_api_key(api_key, *args)

    if not final_api_key:
        print("Внимание: GEMINI_API_KEY не передан. Используются значения по умолчанию.")
        return {}

    client = genai.Client(api_key=final_api_key)
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
        
        text = response.text.strip() if response and response.text else ""
        
        # Безопасная очистка markdown тегов ```json ... ```
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\s*```$', '', text)

        return json.loads(text)

    except Exception as e:
        print(f"Ошибка Gemini NLU ({model_name}): {e}")
        return {}


def validate_nlu_input(parsed_data: dict, *args, **kwargs) -> dict:
    """
    Валидирует данные и принудительно подставляет гарантированные дефолты для отсутствующих полей.
    """
    if not isinstance(parsed_data, dict):
        parsed_data = {}

    # Заполнение станций
    parsed_data["route_from"] = normalize_st_name(parsed_data.get("route_from") or "Bakı-Yük")
    parsed_data["route_to"] = normalize_st_name(parsed_data.get("route_to") or "Yalama")

    # Код ГНГ и имя груза
    if not parsed_data.get("cargo_gng_code"):
        parsed_data["cargo_gng_code"] = "2710"
    if not parsed_data.get("cargo_name"):
        parsed_data["cargo_name"] = "Neft məhsulları"

    # Вес
    try:
        parsed_data["actual_weight_tons"] = float(parsed_data.get("actual_weight_tons") or 55.0)
    except (ValueError, TypeError):
        parsed_data["actual_weight_tons"] = 55.0

    # Тип и парк вагона
    parsed_data["wagon_type"] = parsed_data.get("wagon_type") or "cistern"
    parsed_data["park_type"] = parsed_data.get("park_type") or "SPS"

    # Режим и период
    if "explicit_mode" not in parsed_data or parsed_data["explicit_mode"] is None:
        parsed_data["explicit_mode"] = "transit"
    if "requested_period" not in parsed_data or parsed_data["requested_period"] is None:
        parsed_data["requested_period"] = "2026-08"

    return parsed_data


def call_gemini_nlu(user_input: str, api_key: str = None, *args, **kwargs) -> dict:
    """
    Главная точка входа для app.py.
    """
    raw_parsed_data = parse_user_input_with_gemini(user_input, api_key, *args, **kwargs)
    return validate_nlu_input(raw_parsed_data, *args, **kwargs)
