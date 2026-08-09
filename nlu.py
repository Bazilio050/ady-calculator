import os
import json
import google.generativeai as genai

# ==============================================================================
# СИСТЕМНЫЙ ПРОМПТ ДЛЯ GEMINI NLU (ИНСТРУКЦИЯ И ПРАВИЛА МАРШРУТИЗАЦИИ)
# ==============================================================================
GEMINI_SYSTEM_INSTRUCTION = """
Ты — специализированный NLU-парсер железнодорожного тарифного калькулятора Азербайджанских железных дорог (ADY).
Твоя задача — извлечь параметры перевозки из текста пользователя и вернуть СТРОГО валидный JSON.

---

### 1. ПРАВИЛА НОРМАЛИЗАЦИИ СТАНЦИЙ (ОБЯЗАТЕЛЬНО К ИСПОЛНЕНИЮ)
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
  - "سانгачал", "сангачал тер", "sanqaçal" -> **"Sanqaçal"**
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
   - "import", "export", "transit" или null (если режим определяется автоматически по пограничным станциям).

---

### 3. СТРУКТУРА ВЫХОДНОГО JSON

Верни ответ СТРОГО в следующем формате без стороннего текста и markdown-тегов (```json):

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

# ==============================================================================
# ОСНОВНАЯ ФУНКЦИЯ ОБРАБОТКИ ЗАПРОСА ЧЕРЕЗ GEMINI API
# ==============================================================================
def parse_user_input_with_gemini(user_input: str, api_key: str = None) -> dict:
    """
    Отправляет текстовый запрос пользователя в Gemini NLU и возвращает структурированный JSON.
    """
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY не найден в переменных окружения.")

    genai.configure(api_key=api_key)

    # Используем стабильную модель Gemini
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.1  # Низкая температура для максимальной точности
        },
        system_instruction=GEMINI_SYSTEM_INSTRUCTION
    )

    try:
        response = model.generate_content(user_input)
        result_text = response.text.strip()
        
        # Парсим JSON ответ
        parsed_data = json.loads(result_text)
        return parsed_data

    except Exception as e:
        print(f"Ошибка Gemini NLU: {e}")
        # Запасной дефолтный ответ при сбое сети или API
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
