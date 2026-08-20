import json
import re
import time
from google.genai import types
from rail_glossary import get_rail_vocabulary


# ==============================================================================
# === [НАЧАЛО БЛОКА: NLU-01] Защита от сбоев и перегрузок API (Fallback) ===
# Описание: Отправляет запрос к gemini-3.6-flash. В случае ошибок перегрузки 
# 503 (UNAVAILABLE) или таймаутов 504 (DEADLINE_EXCEEDED) делает паузу и повтор.
# ==============================================================================
def _execute_gemini_request_with_fallback(client, contents, config, primary_model="gemini-3.6-flash", fallback_model="gemini-3.6-flash"):
    """
    По умолчанию отправляет запрос к gemini-3.6-flash.
    При возникновении ошибок 503 (перегрузка) или 504 (таймаут) переключается на fallback_model.
    """
    try:
        return client.models.generate_content(
            model=primary_model,
            contents=contents,
            config=config
        )
    except Exception as e:
        err_msg = str(e)
        code = getattr(e, 'code', None)
        # Перехват 503 (UNAVAILABLE) и 504 (DEADLINE_EXCEEDED)
        if code in (503, 504) or any(err in err_msg for err in ["503", "504", "DEADLINE_EXCEEDED", "UNAVAILABLE"]):
            time.sleep(1)
            return client.models.generate_content(
                model=fallback_model,
                contents=contents,
                config=config
            )
        raise e
# === [КОНЕЦ БЛОКА: NLU-01] ====================================================


# ==============================================================================
# === [НАЧАЛО БЛОКА: NLU-02] Текстовый парсинг запросов (call_gemini_nlu) ===
# Описание: Оптимизированный ультра-быстрый вызов Gemini NLU. Тяжеловесный текст 
# вырезан, таймаут снижен с 25с до 8с. Объём токенов снижен с 8000+ до ~300.
# ==============================================================================
def _build_compact_nlu_prompt(target_lang: str, rail_vocab: str, user_input: str) -> str:
    return f"""You are an expert railway freight NLU assistant for Azerbaijan Railways (ADY).
Extract shipment parameters from user text query into JSON matching the schema below.

CRITICAL ROUTING RULES:
1. FIRST station/port mentioned MUST BE 'origin_name', SECOND MUST BE 'dest_name'. NEVER swap them!
2. Station ESR mapping: Yalama=545006, Abşeron=548004, Biləcəri=546808, Böyük Kəsik=558701, Astara=554109.
3. ALAT (ƏLƏT) DISAMBIGUATION:
   - "Alat-yeni" / "Ələt-yeni" / "новый" -> ESR "548703"
   - "Alat-eksp" / "порт" / "паром" / "bərə" / "Aktau" / "Kurik" / "TRK" -> Port ESR ("549204"/"553002"/"548803") & 'explicit_mode': "transit"
   - Plain "Alat" / "Ələt" / "Алят" -> ESR "548502" (DO NOT set 'transit')

CARGO & WAGON RULES:
- Extract numeric cargo codes to 'gng_code' (strictly digits).
- Match cargo text ("арматура", "пшеница") against Glossary: {rail_vocab}
- TERMS like "крытый", "полувагон", "платформа", "цистерна" are 'wagon_type', NEVER cargo!

JSON SCHEMA:
{{
  "origin_esr": "6-digit string or null", "origin_name": "Station name in {target_lang}",
  "dest_esr": "6-digit string or null", "dest_name": "Station name in {target_lang}",
  "gng_code": "Numeric GNG string only or null", "gng_name": "Cargo name in {target_lang}",
  "weight_tons": float or null,
  "wagon_type": "universal / tank / ref / thermos / autocarrier / transporter",
  "park_type": "SPS / MPS", "ref_section_cargo_wagons": integer or null,
  "explicit_mode": "import / export / transit or null",
  "is_empty": boolean, "axles_count": integer or null,
  "is_own_axles": boolean, "is_in_repair": boolean, "is_passenger_train": boolean,
  "is_consolidated": boolean, "escort_count": integer or 0,
  "has_teplushka": boolean, "teplushka_type": "freight_sps / freight_mps / passenger_sps / passenger_mps or null"
}}

Return ONLY valid JSON. Target language: {target_lang}.
User query: "{user_input}"
"""


def call_gemini_nlu(client, user_input: str, lang: str = "AZ") -> dict:
    """
    Оптимизированный быстрый текстовый парсер NLU.
    """
    lang_map = {"AZ": "Azerbaijani", "RU": "Russian", "EN": "English"}
    target_lang = lang_map.get(str(lang).upper(), "Azerbaijani")
    rail_vocab = get_rail_vocabulary()

    prompt = _build_compact_nlu_prompt(target_lang, rail_vocab, user_input)

    # Таймаут снижен до 8 000 мс (8 секунд) для мгновенного отклика
    config = types.GenerateContentConfig(
        temperature=0.0,
        response_mime_type="application/json",
        http_options=types.HttpOptions(timeout=8000)
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

    wagon_words = ["qapalı vaqon", "крытый вагон", "крытый", "qapalı", "полувагон", "платформа"]
    if "gng_name" in result and result["gng_name"]:
        if any(w in str(result["gng_name"]).lower() for w in wagon_words):
            result["gng_name"] = "Buğda" if result.get("gng_code") == "1001" else ""

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
# Описание: Принимает байты голосового сообщения, транскрибирует речь в текст 
# (transcript) и одновременно извлекает все параметры железнодорожной перевозки.
# ==============================================================================
def call_gemini_audio_nlu(client, audio_bytes: bytes, mime_type: str = "audio/wav", lang: str = "AZ") -> dict:
    """
    Принимает байты аудиозаписи.
    """
    lang_map = {"AZ": "Azerbaijani", "RU": "Russian", "EN": "English"}
    target_lang = lang_map.get(str(lang).upper(), "Azerbaijani")
    rail_vocab = get_rail_vocabulary()

    prompt = f"""
    You are an expert railway freight NLU assistant for Azerbaijan Railways (ADY).
    Listen carefully to the audio input containing a freight shipment request.

    ACTIVE RAILWAY TERMINOLOGY & VOCABULARY REFERENCE:
    {rail_vocab}

    Tasks:
    1. Transcribe the spoken text accurately into the 'transcript' field.
    2. Extract shipment parameters into a JSON object matching the schema below.

    CRITICAL RULES FOR STATIONS & ROUTING:
    - STRICT ORDER RULE: The FIRST station or Caspian ferry port mentioned in the audio MUST ALWAYS be assigned to 'origin_name'. The SECOND station/port MUST ALWAYS be assigned to 'dest_name'.
    - NEVER swap origin and destination stations!
    - Station ESR codes mapping: 
      Yalama=545006, Abşeron=548004, Biləcəri=546808, Böyük Kəsik=558701, Astara=554109,
      Alat-yeni/Ələt-yeni/Алят-новый=548703, Kurik/Kuryk/Курык=553002, Aktau/Актау=549204, Türkmenbaşı/Turkmenbashi/TRK/ТРК=548803.

    CRITICAL DISAMBIGUATION RULE FOR ALAT (ƏLƏT / АЛЯТ):
    - IF user explicitly mentions "Alat-yeni", "Ələt-yeni", "Алят-новый", or "новый":
      Assign code "548703" to origin_esr or dest_esr depending on position.
    - IF user mentions "Alat-eksp", "Ələt-eksp", "порт", "паром", "bərə", "Aktau", "Kurik", or "TRK":
      1. Assign port ESR code (549204 / 553002 / 548803) to origin_esr or dest_esr depending on position.
      2. Set 'explicit_mode': "transit".
    - IF user mentions plain "Alat" / "Ələt" / "Алят" WITHOUT words like "yeni/новый", "эксп", "порт", "паром", "bərə":
      1. Assign ESR code "548502" to origin_esr or dest_esr depending on position.
      2. DO NOT set 'explicit_mode' to "transit".

    EXPECTED JSON STRUCTURE:
    {{
      "transcript": "Exact transcribed text from audio",
      "origin_esr": "6-digit ESR string or null",
      "origin_name": "Station name in {target_lang}",
      "dest_esr": "6-digit ESR string or null",
      "dest_name": "Station name in {target_lang}",
      "gng_code": "Numeric GNG code string only or null",
      "gng_name": "Cargo name in {target_lang}",
      "weight_tons": float or null,
      "wagon_type": "universal / tank / ref / thermos / autocarrier / transporter",
      "park_type": "SPS / MPS",
      "ref_section_cargo_wagons": integer or null,
      "explicit_mode": "import / export / transit or null",
      "is_empty": boolean,
      "axles_count": integer or null,
      "is_own_axles": boolean,
      "is_in_repair": boolean,
      "is_passenger_train": boolean,
      "is_consolidated": boolean,
      "escort_count": integer or 0,
      "has_teplushka": boolean,
      "teplushka_type": "freight_sps / freight_mps / passenger_sps / passenger_mps or null"
    }}

    Return ONLY a valid JSON object. User language context: {target_lang}.
    """

    config = types.GenerateContentConfig(
        temperature=0.0,
        response_mime_type="application/json",
        http_options=types.HttpOptions(timeout=35000)
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
