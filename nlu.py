import json
import re
from google.genai import types

def call_gemini_nlu(client, user_input: str, lang: str = "AZ") -> dict:
    """
    Анализирует текстовый запрос пользователя и возвращает JSON с параметрами перевозки.
    """
    lang_map = {"AZ": "Azerbaijani", "RU": "Russian", "EN": "English"}
    target_lang = lang_map.get(str(lang).upper(), "Azerbaijani")

    prompt = f"""
    You are an expert railway freight NLU assistant for Azerbaijan Railways (ADY).
    Analyze the user text query containing a freight shipment request.

    Extract parameters into a JSON object matching the schema below.

    CRITICAL RULES FOR GNG & ESR CODES:
    - ALWAYS extract any cargo numeric code into 'gng_code' (e.g. if query contains "4407" or "GNG 4407", set 'gng_code': "4407").
    - NEVER put text descriptions into 'gng_code'! Keep 'gng_code' STRICTLY NUMERIC.
    - Station ESR codes: Yalama=545006, Abşeron=548004, Biləcəri=546808, Böyük Kəsik=558701, Astara=554109.

    EXPECTED JSON STRUCTURE:
    {{
      "origin_esr": "6-digit ESR string or null",
      "origin_name": "Station name in {target_lang}",
      "dest_esr": "6-digit ESR string or null",
      "dest_name": "Station name in {target_lang}",
      "gng_code": "Numeric GNG code string only (e.g., '4407', '2713') or null",
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

    # Жесткая очистка gng_code до чистых цифр
    if "gng_code" in result and result["gng_code"]:
        result["gng_code"] = re.sub(r'\D', '', str(result["gng_code"]))

    # Защита полей
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
    Принимает байты аудиозаписи, выполняет транскрибацию и предварительный NLU-анализ.
    """
    lang_map = {"AZ": "Azerbaijani", "RU": "Russian", "EN": "English"}
    target_lang = lang_map.get(str(lang).upper(), "Azerbaijani")

    prompt = f"""
    You are an expert railway freight NLU assistant for Azerbaijan Railways (ADY).
    Listen carefully to the audio input containing a freight shipment request.

    Tasks:
    1. Transcribe the spoken text accurately into the 'transcript' field.
    2. Extract shipment parameters into a JSON object matching the schema below.

    CRITICAL RULES FOR GNG & ESR CODES:
    - ALWAYS extract any spoken cargo numeric code into 'gng_code' (e.g. if user says "4407" or "GNG 4407", set 'gng_code': "4407"). Never put text descriptions into 'gng_code'!
    - If user speaks numbers phonetically or with noise (e.g. "sorğu 07" for 4407), do your best to extract the numeric GNG code.
    - Station ESR codes: Yalama=545006, Abşeron=548004, Biləcəri=546808, Böyük Kəsik=558701, Astara=554109.

    EXPECTED JSON STRUCTURE:
    {{
      "transcript": "Exact transcribed text spoken by user",
      "origin_esr": "6-digit ESR string or null",
      "origin_name": "Station name in {target_lang}",
      "dest_esr": "6-digit ESR string or null",
      "dest_name": "Station name in {target_lang}",
      "gng_code": "Numeric GNG code string only (e.g., '4407', '2713') or null",
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

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[audio_part, prompt],
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

    # Жесткая очистка gng_code до чистых цифр
    if "gng_code" in result and result["gng_code"]:
        result["gng_code"] = re.sub(r'\D', '', str(result["gng_code"]))

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
    """
    Проверяет минимально необходимые данные для расчета.
    """
    missing = []
    
    origin = nlu_data.get("origin_name") or nlu_data.get("origin_esr")
    dest = nlu_data.get("dest_name") or nlu_data.get("dest_esr")
    
    if not origin:
        missing.append("Məlumat yoxdur: Göndərmə stansiyası" if lang == "AZ" else "Отсутствует станция отправления")
    if not dest:
        missing.append("Məlumat yoxdur: Təyinat stansiyası" if lang == "AZ" else "Отсутствует станция назначения")
        
    return missing
