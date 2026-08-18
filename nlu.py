import json
import re
from google.genai import types
from rail_glossary import get_rail_vocabulary

def call_gemini_nlu(client, user_input: str, lang: str = "AZ") -> dict:
    """
    Анализирует текстовый запрос пользователя через быструю модель gemini-3.5-flash-lite.
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
      Kurik/Kuryk/Курык=553002, Aktau/Актау=549204, Türkmenbaşı/Turkmenbashi/TRK/ТРК=548803.

    CRITICAL RULES FOR GNG, CARGO NAME & WAGON TYPE:
    - ALWAYS extract any cargo numeric code into 'gng_code' (e.g. if query contains "1001" or "GNG 1001", set 'gng_code': "1001").
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
      "gng_code": "Numeric GNG code string only (e.g., '1001', '4407') or null",
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

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json"
        )
    )

    raw_text = response.text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]

    result = json.loads(raw_text.strip())
    result["site_lang"] = str(lang).upper()

    # Сбор метаданных использования токенов
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        result["_usage"] = {
            "input": response.usage_metadata.prompt_token_count,
            "output": response.usage_metadata.candidates_token_count
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
    Принимает байты аудиозаписи и выполняет распознавание через мощную мультимодальную модель gemini-3.6-flash.
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
      Kurik/Kuryk/Курык=553002, Aktau/Актау=549204, Türkmenbaşı/Turkmenbashi/TRK/ТРК=548803.

    CRITICAL RULES FOR GNG, CARGO NAME & WAGON TYPE:
    - ALWAYS extract any spoken cargo numeric code into 'gng_code' (e.g. if user says "1001" or "GNG 1001", set 'gng_code': "1001"). Never put text descriptions into 'gng_code'!
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
      "gng_code": "Numeric GNG code string only (e.g., '1001', '2713') or null",
      "gng_name": "Cargo name in {target_lang}",
      "weight_tons": float or null,
      "wagon_type": "universal / tank / ref / thermos / autocarrier / transporter",
      "park_type": "SPS / MPS",
      "ref_section_cargo_wagons": integer or null,
      "explicit
