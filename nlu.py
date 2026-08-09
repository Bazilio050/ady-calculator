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

### 2. СТРУКТУРА ВЫХОДНОГО JSON

Верни ответ СТРОГО в следующем формате без markdown-тегов:

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


def _get_api_key(api_key: str = None, *args) -> str:
    """Извлекает API ключ из аргументов, os.getenv или st.secrets."""
    for key in [api_key] + list(args):
        if key and isinstance(key, str) and len(key) > 10 and key.lower() not in ["az", "ru", "en"]:
            return key
    
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key:
        return env_key

    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    return ""


def parse_user_input_with_gemini(user_input: str, api_key: str = None, *args, **kwargs) -> dict:
    """
    Парсит запрос пользователя СТРОГО через gemini-3.5-flash-lite без переключения на другие модели.
    """
    final_key = _get_api_key(api_key, *args)
    if not final_key:
        print("API ключ не найден.")
        return {}

    try:
        client = genai.Client(api_key=final_key)
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
            system_instruction=GEMINI_SYSTEM_INSTRUCTION
        )

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=user_input,
            config=config
        )
        
        text = response.text.strip() if response and response.text else ""
        
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\s*```$', '', text)

        data = json.loads(text)
        if isinstance(data, dict) and len(data) > 0:
            return data

    except Exception as e:
        print(f"Ошибка Gemini NLU (gemini-3.5-flash-lite): {e}")

    return {}


def validate_nlu_input(parsed_data: dict, *args, **kwargs) -> dict:
    """
    Гарантирует заполнение всех обязательных ключей дефолтными значениями.
    """
    if not isinstance(parsed_data, dict):
        parsed_data = {}

    res = {}
    res["route_from"] = normalize_st_name(parsed_data.get("route_from") or "Bakı-Yük")
    res["route_to"] = normalize_st_name(parsed_data.get("route_to") or "Yalama")
    res["cargo_gng_code"] = str(parsed_data.get("cargo_gng_code") or "2710")
    res["cargo_name"] = str(parsed_data.get("cargo_name") or "Neft məhsulları")

    try:
        res["actual_weight_tons"] = float(parsed_data.get("actual_weight_tons") or 55.0)
    except (ValueError, TypeError):
        res["actual_weight_tons"] = 55.0

    res["wagon_type"] = parsed_data.get("wagon_type") or "cistern"
    res["park_type"] = parsed_data.get("park_type") or "SPS"
    res["explicit_mode"] = parsed_data.get("explicit_mode") or "transit"
    res["requested_period"] = parsed_data.get("requested_period") or "2026-08"

    return res


def call_gemini_nlu(user_input: str, api_key: str = None, *args, **kwargs) -> dict:
    """
    Главная внешняя функция.
    """
    raw_parsed_data = parse_user_input_with_gemini(user_input, api_key, *args, **kwargs)
    return validate_nlu_input(raw_parsed_data, *args, **kwargs)
