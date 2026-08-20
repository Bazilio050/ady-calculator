import json
import re
import time
from google.genai import types
from rail_glossary import get_rail_vocabulary


# ==============================================================================
# === [НАЧАЛО БЛОКА: NLU-01] Защита от сбоев и перегрузок API (Fallback) ===
# Описание: Отправляет запрос к gemini-3.6-flash. В случае перегрузок делает паузу.
# ==============================================================================
def _execute_gemini_request_with_fallback(
    client, 
    contents, 
    config, 
    primary_model="gemini-3.6-flash", 
    fallback_model="gemini-3.6-flash"
):
    try:
        return client.models.generate_content(
            model=primary_model,
            contents=contents,
            config=config
        )
    except Exception as e:
        err_msg = str(e)
        code = getattr(e, 'code', None)
        
        is_rate_limit = code == 429 or any(err in err_msg for err in ["429", "RESOURCE_EXHAUSTED", "ResourceExhausted", "Quota exceeded"])
        is_server_error = code in (499, 503, 504) or any(err in err_msg for err in ["499", "503", "504", "CANCELLED", "DEADLINE_EXCEEDED", "UNAVAILABLE"])

        if is_rate_limit or is_server_error:
            time.sleep(2.5)
            try:
                return client.models.generate_content(
                    model=fallback_model,
                    contents=contents,
                    config=config
                )
            except Exception as retry_err:
                raise retry_err
        raise e
# === [КОНЕЦ БЛОКА: NLU-01] ====================================================


# ==============================================================================
# === [НАЧАЛО БЛОКА: NLU-02] Компактный NLU-промпт (Порты + Метраж + Режим) ===
# Описание: Распознает станции, порты, метраж и явное указание режима (explicit_mode).
# ==============================================================================
def _build_compact_nlu_prompt(target_lang: str, user_input: str) -> str:
    return f"""Ты — NLU-парсер ж/д запросов для Азербайджана (ADY).
Извлеки из текста параметры в JSON:
1. origin_name: Первая станция или порт отправления (например, "Ялама", "Беюк Кясик", "Алят-порт", "Курык").
2. dest_name: Вторая станция или порт назначения (например, "Беюк Кясик", "Астара", "Актау", "Туркменбаши").
3. gng_code: Код ГНГ (строго цифры, напр. "4407", "7201").
4. weight_tons: Вес груза в тоннах (число).
5. wagon_type: Тип вагона ("universal", "tank", "ref", "thermos", "transporter", "autocarrier").
6. park_type: "SPS" или "MPS".
7. is_empty: true если вагон порожний, иначе false.
8. wagon_length_m: Длина вагона/платформы в метрах (число, напр. 14.5, 19.0, 24.0 или null).
9. explicit_mode: "export", "import", "transit" или null. Явно заполнять если в тексте есть слова "экспорт"/"ixrac", "импорт"/"idxal", "транзит"/"tranzit".

ПОДСКАЗКА ПО ПОРТАМ:
- "ТРК", "TRK", "Туркменбаши" -> порт Туркменбаши.
- "Курык", "Kuryk", "Quruq" -> порт Курык.
- "Актау", "Aktau" -> порт Актау.

ПРАВИЛО: Выводи ТОЛЬКО чистый JSON. Никаких приветствий и пояснений.
Язык названий: {target_lang}.
Запрос: "{user_input}"
"""


def call_gemini_nlu(client, user_input: str, lang: str = "AZ") -> dict:
    lang_map = {"AZ": "Azerbaijani", "RU": "Russian", "EN": "English"}
    target_lang = lang_map.get(str(lang).upper(), "Azerbaijani")

    prompt = _build_compact_nlu_prompt(target_lang, user_input)

    config = types.GenerateContentConfig(
        temperature=0.0,
        response_mime_type="application/json",
        http_options=types.HttpOptions(timeout=30000)
    )

    response = _execute_gemini_request_with_fallback(client, prompt, config)

    raw_text = response.text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]

    result = json.loads(raw_text.strip())
    result["site_lang"] = str(lang).upper()

    if hasattr(response, "usage_metadata") and response.usage_metadata:
        result["_usage"] = {
            "input": getattr(response.usage_metadata, "prompt_token_count", 0),
            "output": getattr(response.usage_metadata, "candidates_token_count", 0)
        }

    if "gng_code" in result and result["gng_code"]:
        result["gng_code"] = re.sub(r'\D', '', str(result["gng_code"]))

    if "explicit_mode" not in result or not result["explicit_mode"]:
        result["explicit_mode"] = None
    else:
        mode_clean = str(result["explicit_mode"]).lower()
        if any(k in mode_clean for k in ["export", "ixrac", "экспорт"]):
            result["explicit_mode"] = "export"
        elif any(k in mode_clean for k in ["import", "idxal", "импорт"]):
            result["explicit_mode"] = "import"
        elif any(k in mode_clean for k in ["transit", "tranzit", "транзит"]):
            result["explicit_mode"] = "transit"

    if "wagon_length_m" not in result or result["wagon_length_m"] is None:
        result["wagon_length_m"] = None

    if "escort_count" not in result or result["escort_count"] is None:
        result["escort_count"] = 0
    if "has_teplushka" not in result or result["has_teplushka"] is None:
        result["has_teplushka"] = False
    if "teplushka_type" not in result or not result["teplushka_type"]:
        result["teplushka_type"] = "freight_sps"
    if "is_empty" not in result or result["is_empty"] is None:
        result["is_empty"] = False
    if "is_own_axles" not in result or result["is_own_axles"] is None:
        result["is_own_axles"] = False

    return result
# === [КОНЕЦ БЛОКА: NLU-02] ====================================================


# ==============================================================================
# === [НАЧАЛО БЛОКА: NLU-03] Голосовой парсинг (call_gemini_audio_nlu) ===
# Описание: Выполняет голосовой парсинг без привязки к хардкод-кодам ЕСР.
# ==============================================================================
def call_gemini_audio_nlu(client, audio_bytes: bytes, mime_type: str = "audio/wav", lang: str = "AZ") -> dict:
    lang_map = {"AZ": "Azerbaijani", "RU": "Russian", "EN": "English"}
    target_lang = lang_map.get(str(lang).upper(), "Azerbaijani")
    rail_vocab = get_rail_vocabulary()

    prompt = f"""You are an expert railway freight NLU assistant for Azerbaijan Railways (ADY).
Listen carefully to the audio input containing a freight shipment request.

Tasks:
1. Transcribe spoken text accurately into 'transcript' field.
2. Extract shipment parameters into JSON matching schema below.

ROUTING & CARGO RULES:
- FIRST station mentioned = 'origin_name', SECOND = 'dest_name'.
- ALAT (ƏLƏT): "yeni" -> 'origin_name': "Ələt yeni"; "eksp/порт/паром/Aktau/Kurik/TRK" -> 'explicit_mode': "transit".
- Match cargo terms against Vocabulary: {rail_vocab}

EXPECTED JSON SCHEMA:
{{
  "transcript": "Exact transcribed text",
  "origin_name": "Station name in {target_lang}",
  "dest_name": "Station name in {target_lang}",
  "gng_code": "Numeric GNG string or null",
  "gng_name": "Cargo name in {target_lang}",
  "weight_tons": float or null,
  "wagon_type": "universal / tank / ref / thermos / autocarrier / transporter",
  "park_type": "SPS / MPS",
  "explicit_mode": "import / export / transit or null",
  "is_empty": boolean,
  "axles_count": integer or null,
  "is_own_axles": boolean
}}
Return ONLY valid JSON. Target language: {target_lang}."""

    config = types.GenerateContentConfig(
        temperature=0.0,
        response_mime_type="application/json",
        http_options=types.HttpOptions(timeout=20000)
    )

    audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
    response = _execute_gemini_request_with_fallback(client, [prompt, audio_part], config)

    raw_text = response.text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]

    result = json.loads(raw_text.strip())
    result["site_lang"] = str(lang).upper()

    if hasattr(response, "usage_metadata") and response.usage_metadata:
        result["_usage"] = {
            "input": getattr(response.usage_metadata, "prompt_token_count", 0),
            "output": getattr(response.usage_metadata, "candidates_token_count", 0)
        }

    return result
# === [КОНЕЦ БЛОКА: NLU-03] ====================================================


# ==============================================================================
# === [НАЧАЛО БЛОКА: NLU-04] Валидация входных параметров NLU ===
# ==============================================================================
def validate_nlu_input(nlu_data: dict, lang: str = "AZ") -> list:
    missing = []
    
    if not isinstance(nlu_data, dict):
        return ["Некорректный формат данных от NLU"]

    if not nlu_data.get("origin_name") and not nlu_data.get("origin_esr"):
        missing.append("Станция отправления (Origin)")
    if not nlu_data.get("dest_name") and not nlu_data.get("dest_esr"):
        missing.append("Станция назначения (Destination)")

    return missing
# === [КОНЕЦ БЛОКА: NLU-04] ====================================================
