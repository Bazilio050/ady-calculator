import json
import re
import time
from google.genai import types
from google.genai.errors import APIError
from rail_glossary import get_rail_vocabulary

def _execute_gemini_request_with_fallback(client, contents, config, primary_model="gemini-3.7-flash", fallback_model="gemini-3.6-flash"):
    """
    По умолчанию делает запрос к gemini-3.7-flash.
    Если сервера перегружены (ошибка 503), автоматически переключается на gemini-3.6-flash.
    """
    try:
        return client.models.generate_content(
            model=primary_model,
            contents=contents,
            config=config
        )
    except APIError as e:
        if getattr(e, 'code', None) == 503 or "503" in str(e):
            time.sleep(1)
            return client.models.generate_content(
                model=fallback_model,
                contents=contents,
                config=config
            )
        raise e

def call_gemini_nlu(client, user_input: str, lang: str = "AZ") -> dict:
    """
    Анализирует текстовый запрос пользователя. По умолчанию 3.7, фоллбэк на 3.6.
    """
    lang_map = {"AZ": "Azerbaijani", "RU": "Russian", "EN": "English"}
    target_lang = lang_map.get(str(lang).upper(), "Azerbaijani")
    rail_vocab = get_rail_vocabulary()

    prompt = f"""
    You are an expert railway freight NLU assistant for Azerbaijan Railways (ADY).
    Analyze the user text query containing a freight shipment request.

    ACTIVE RAILWAY TERMINOLOGY & VOCABULARY REFERENCE:
    {rail_vocab}

    Extract parameters into a JSON object matching the schema below.

    CRITICAL RULES FOR STATIONS & ROUTING:
    - STRICT ORDER RULE: The FIRST station or Caspian ferry port mentioned in the text MUST ALWAYS be assigned to 'origin_name'. The SECOND station/port MUST ALWAYS be assigned to 'dest_name'.
    - NEVER swap origin and destination stations!
    - Station ESR codes mapping: 
      Yalama=545006, Abşeron=548004, Biləcəri=546808, Böyük Kəsik=558701, Astara=554109,
      Alat-yeni/Ələt-yeni/Алят-новый=548703, Kurik/Kuryk/Курык=553002, Aktau/Актау=549204, Türkmenbaşı/Turkmenbashi/TRK/ТРК=548803.

    CRITICAL DISAMBIGUATION RULE FOR ALAT (ƏLƏT / АЛЯТ):
    - IF user explicitly mentions "Alat-yeni", "Ələt-yeni", "Алят-новый", or "новый":
      Assign 'dest_esr': "548703" (distance 266 km).
    - IF user mentions "Alat" / "Ələt" / "Алят" WITHOUT explicit words "import", "export", "idxal", "ixrac", or "yeni/новый":
      1. Assign 'dest_esr': "553002" (Ələt-liman / Alat Port export junction, distance 271 km).
      2. Set 'explicit_mode': "transit".
    - IF user explicitly includes "import", "export", "idxal", or "ixrac" alongside Alat (without "yeni/новый"):
      1. Assign 'dest_esr': "548502" (Ələt land station, distance 261 km).
      2. Set 'explicit_mode': "import" or "export".

    CRITICAL RULES FOR GNG, CARGO NAME & WAGON TYPE:
    - ALWAYS extract any cargo numeric code into 'gng_code' (e.g. if query contains "1001" or "GNG 1001", set 'gng_code': "1001").
    - CARGO LOOKUP RULE: If NO numeric GNG code is explicitly written, but a cargo name/description is mentioned (e.g., "прокат", "арматура", "пшеница", "цемент"), YOU MUST MATCH IT against the railway glossary reference and set 'gng_code' to its 4-digit or 8-digit numeric code! DO NOT return null or "00000000" if cargo name is present!
    - NEVER put text descriptions or wagon terms into 'gng_code'! Keep 'gng_code' STRICTLY NUMERIC.
    - STRICT PRIORITY RULE FOR GNG: The abbreviation 'GNG', 'NHM' or 'ГНГ' followed by numbers represents strictly a cargo nomenclature code. It is STRICTLY FORBIDDEN to interpret 'GNG' as the city of Ganja (Gəncə) or any other similar-sounding word.
    - TERMS LIKE "qapalı vaqon", "крытый вагон", "полувагон", "платформа", "цистерна", "çən", "cistern" ARE WAGON TYPES ('wagon_type'), NEVER CARGO NAMES ('gng_name')!
    - If GNG 1001 is provided without an explicit cargo description, set 'gng_name': "Buğda".

    EXPECTED JSON STRUCTURE:
    {{
      "origin_esr": "6-digit ESR string or null",
      "origin_name": "Station name in {target_lang}",
      "dest_esr": "6-digit ESR string or null",
      "dest_name": "Station name in {target_lang}",
      "gng_code": "Numeric GNG code string only (e.g., '1001', '4407', '7208') or null",
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
    Query: "{user_input}"
    """

    config = types.GenerateContentConfig(
        temperature=0.0,
        response_mime_type="application/json",
        http_options=types.HttpOptions(timeout=12000)
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


def call_gemini_audio_nlu(client, audio_bytes: bytes, mime_type: str = "audio/wav", lang: str = "AZ") -> dict:
    """
    Принимает байты аудиозаписи. По умолчанию 3.7, фоллбэк на 3.6.
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
      Assign 'dest_esr': "548703" (distance 266 km).
    - IF user mentions "Alat" / "Ələt" / "Алят" WITHOUT explicit words "import", "export", "idxal", "ixrac", or "yeni/новый":
      1. Assign 'dest_esr': "553002" (Ələt-liman / Alat Port export junction, distance 271 km).
      2. Set 'explicit_mode': "transit".
    - IF user explicitly includes "import", "export", "idxal", or "ixrac" alongside Alat (without "yeni/новый"):
      1. Assign 'dest_esr': "548502" (Ələt land station, distance 261 km).
      2. Set 'explicit_mode': "import" or "export".

    CRITICAL RULES FOR GNG, CARGO NAME & WAGON TYPE:
    - ALWAYS extract any spoken cargo numeric code into 'gng_code' (e.g. if user says "1001" or "GNG 1001", set 'gng_code': "1001").
    - CARGO LOOKUP RULE: If NO numeric GNG code is spoken, but a cargo name/description is mentioned (e.g., "прокат", "арматура", "пшеница", "цемент"), YOU MUST MATCH IT against the railway glossary reference and set 'gng_code' to its numeric code!
    - STRICT PRIORITY RULE FOR GNG: Spoken 'GNG', 'NHM' or 'ГНГ' followed by numbers represents strictly a cargo nomenclature code. It is STRICTLY FORBIDDEN to interpret 'GNG' as the city of Ganja (Gəncə) or any other similar-sounding word.
    - TERMS LIKE "qapalı vaqon", "крытый вагон", "полувагон", "платформа", "цистерна", "çən", "cistern" ARE WAGON TYPES ('wagon_type'), NEVER CARGO NAMES ('gng_name')!
    - If GNG 1001 is provided without an explicit cargo description, set 'gng_name': "Buğda".

    EXPECTED JSON STRUCTURE:
    {{
      "transcript": "Exact transcribed text spoken by user",
      "origin_esr": "6-digit ESR string or null",
      "origin_name": "Station name in {target_lang}",
      "dest_esr": "6-digit ESR string or null",
      "dest_name": "Station name in {target_lang}",
      "gng_code": "Numeric GNG code string only (e.g., '1001', '2713', '7208') or null",
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

    Return ONLY a valid JSON object. UI language context: {target_lang}.
    """

    audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

    config = types.GenerateContentConfig(
        temperature=0.0,
        response_mime_type="application/json",
        http_options=types.HttpOptions(timeout=15000)
    )

    contents = [audio_part, prompt]
    response = _execute_gemini_request_with_fallback(client, contents, config)

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

def validate_nlu_input(nlu_data: dict, lang: str = "AZ") -> list:
    missing = []
    origin = nlu_data.get("origin_name") or nlu_data.get("origin_esr")
    dest = nlu_data.get("dest_name") or nlu_data.get("dest_esr")
    
    if not origin:
        missing.append("Məlumat yoxdur: Göndərmə stansiyası" if lang == "AZ" else "Отсутствует станция отправления")
    if not dest:
        missing.append("Məlumat yoxdur: Təyinat stansiyası" if lang == "AZ" else "Отсутствует станция назначения")
        
    return missing
