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

    prompt = (
        "You are an expert railway & Caspian ferry freight NLU assistant for Azerbaijan Railways (ADY) and ASCO.\n"
        "Analyze the user text query containing a freight shipment request.\n\n"
        "ACTIVE RAILWAY TERMINOLOGY & VOCABULARY REFERENCE:\n"
        + str(rail_vocab) + "\n\n"
        "Extract parameters into a JSON object matching the schema below.\n\n"
        "CRITICAL RULES FOR GNG, CARGO NAME & WAGON TYPE:\n"
        "- ALWAYS extract any cargo numeric code into 'gng_code' (e.g. if query contains \"1001\" or \"GNG 1001\", set 'gng_code': \"1001\").\n"
        "- NEVER put text descriptions or wagon terms into 'gng_code'! Keep 'gng_code' STRICTLY NUMERIC.\n"
        "- STRICT PRIORITY RULE FOR GNG: The abbreviation 'GNG', 'NHM' or 'ГНГ' followed by numbers represents strictly a cargo nomenclature code. It is STRICTLY FORBIDDEN to interpret 'GNG' as the city of Ganja (Gəncə) or any other similar-sounding word.\n"
        "- TERMS LIKE \"qapalı vaqon\", \"крытый вагон\", \"полувагон\", \"платформа\", \"цистерна\", \"çən\", \"cistern\" ARE WAGON TYPES ('wagon_type'), NEVER CARGO NAMES ('gng_name')!\n"
        "- If GNG 1001 is provided without an explicit cargo description, set 'gng_name': \"Buğda\".\n"
        "- Station ESR codes: Yalama=545006, Abşeron=548004, Biləcəri=546808, Böyük Kəsik=558701, Astara=554109, Ələt (Bərə/Паром)=549204.\n\n"
        "CRITICAL RULES FOR ASCO CASPIAN FERRY:\n"
        "- Set 'is_asco_ferry': true if the request mentions ferry crossing or Caspian sea ports: \"Quruq\", \"Kuryk\", \"Курык\", \"Aqtau\", \"Aktau\", \"Актау\", \"Türkmenbaşı\", \"Turkmenbashi\", \"Туркменбаши\", \"TRK\", \"ТРК\", \"bərə\", \"паром\", \"ferry\".\n"
        "- Extract wagon length in meters into 'wagon_length_meters' as a float (e.g. \"15m\", \"17 м\", \"16.97m\" -> 15.0, 17.0, 16.97). If not explicitly mentioned, set 'wagon_length_meters': null.\n\n"
        "EXPECTED JSON STRUCTURE:\n"
        "{\n"
        '  "origin_esr": "6-digit ESR string or null",\n'
        '  "origin_name": "Station name in ' + target_lang + '",\n'
        '  "dest_esr": "6-digit ESR string or null",\n'
        '  "dest_name": "Station name in ' + target_lang + '",\n'
        '  "gng_code": "Numeric GNG code string only (e.g., \'1001\', \'4407\') or null",\n'
        '  "gng_name": "Cargo name in ' + target_lang + '",\n'
        '  "weight_tons": float or null,\n'
        '  "wagon_type": "universal / tank / ref / thermos / autocarrier / transporter",\n'
        '  "park_type": "SPS / MPS",\n'
        '  "ref_section_cargo_wagons": integer or null,\n'
        '  "explicit_mode": "import / export / transit or null",\n'
        '  "is_empty": boolean,\n'
        '  "axles_count": integer or null,\n'
        '  "is_own_axles": boolean,\n'
        '  "is_in_repair": boolean,\n'
        '  "is_passenger_train": boolean,\n'
        '  "is_consolidated": boolean,\n'
        '  "escort_count": integer or 0,\n'
        '  "has_teplushka": boolean,\n'
        '  "teplushka_type": "freight_sps / freight_mps / passenger_sps / passenger_mps or null",\n'
        '  "is_asco_ferry": boolean,\n'
        '  "wagon_length_meters": float or null\n'
        "}\n\n"
        "Return ONLY a valid JSON object. User language context: " + target_lang + ".\n"
        'Query: "' + str(user_input) + '"\n'
    )

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
    if "is_asco_ferry" not in result or result["is_asco_ferry"] is None:
        result["is_asco_ferry"] = False
    if "wagon_length_meters" not in result:
        result["wagon_length_meters"] = None

    ferry_keywords = ["quruq", "kuryk", "курык", "aqtau", "aktau", "актау", "türkmenbaşı", "turkmenbashi", "туркменбаши", "trk", "трк", "bərə", "паром", "ferry"]
    if any(k in str(user_input).lower() for k in ferry_keywords):
        result["is_asco_ferry"] = True

    return result


def call_gemini_audio_nlu(client, audio_bytes: bytes, mime_type: str = "audio/wav", lang: str = "AZ") -> dict:
    """
    Принимает байты аудиозаписи и выполняет распознавание через мультимодальную модель gemini-3.6-flash.
    """
    lang_map = {"AZ": "Azerbaijani", "RU": "Russian", "EN": "English"}
    target_lang = lang_map.get(str(lang).upper(), "Azerbaijani")
    rail_vocab = get_rail_vocabulary()

    prompt = (
        "You are an expert railway & Caspian ferry freight NLU assistant for Azerbaijan Railways (ADY) and ASCO.\n"
        "Listen carefully to the audio input containing a freight shipment request.\n\n"
        "ACTIVE RAILWAY TERMINOLOGY & VOCABULARY REFERENCE:\n"
        + str(rail_vocab) + "\n\n"
        "Tasks:\n"
        "1. Transcribe the spoken text accurately into the 'transcript' field.\n"
        "2. Extract shipment parameters into a JSON object matching the schema below.\n\n"
        "CRITICAL RULES FOR GNG, CARGO NAME & WAGON TYPE:\n"
        "- ALWAYS extract any spoken cargo numeric code into 'gng_code' (e.g. if user says \"1001\" or \"GNG 1001\", set 'gng_code': \"1001\"). Never put text descriptions into 'gng_code'!\n"
        "- STRICT PRIORITY RULE FOR GNG: Spoken 'GNG', 'NHM' or 'ГНГ' followed by numbers represents strictly a cargo nomenclature code. It is STRICTLY FORBIDDEN to interpret 'GNG' as the city of Ganja (Gəncə) or any other similar-sounding word.\n"
        "- TERMS LIKE \"qapalı vaqon\", \"крытый вагон\", "полувагон", "платформа", "цистерна", "çən", "cistern" ARE WAGON TYPES ('wagon_type'), NEVER CARGO NAMES ('gng_name')!\n"
        "- If GNG 1001 is provided without an explicit cargo description, set 'gng_name': \"Buğda\".\n"
        "- Station ESR codes: Yalama=545006, Abşeron=548004, Biləcəri=546808, Böyük Kəsik=558701, Astara=554109, Ələt (Bərə/Паром)=549204.\n\n"
        "CRITICAL RULES FOR ASCO CASPIAN FERRY:\n"
        "- Set 'is_asco_ferry': true if the request mentions ferry crossing or Caspian sea ports: \"Quruq\", \"Kuryk\", \"Курык\", \"Aqtau\", \"Aktau\", \"Актау\", \"Türkmenbaşı\", \"Turkmenbashi\", \"Туркменбаши\", \"TRK\", \"ТРК\", \"bərə\", \"паром\", \"ferry\".\n"
        "- Extract wagon length in meters into 'wagon_length_meters' as a float (e.g. \"15m\", \"17 м\", \"16.97m\" -> 15.0, 17.0, 16.97). If not explicitly mentioned, set 'wagon_length_meters': null.\n\n"
        "EXPECTED JSON STRUCTURE:\n"
        "{\n"
        '  "transcript": "Exact transcribed text spoken by user",\n'
        '  "origin_esr": "6-digit ESR string or null",\n'
        '  "origin_name": "Station name in ' + target_lang + '",\n'
        '  "dest_esr": "6-digit ESR string or null",\n'
        '  "dest_name": "Station name in ' + target_lang + '",\n'
        '  "gng_code": "Numeric GNG code string only (e.g., \'1001\', \'2713\') or null",\n'
        '  "gng_name": "Cargo name in ' + target_lang + '",\n'
        '  "weight_tons": float or null,\n'
        '  "wagon_type": "universal / tank / ref / thermos / autocarrier / transporter",\n'
        '  "park_type": "SPS / MPS",\n'
        '  "ref_section_cargo_wagons": integer or null,\n'
        '  "explicit_mode": "import / export / transit or null",\n'
        '  "is_empty": boolean,\n'
        '  "axles_count": integer or null,\n'
        '  "is_own_axles": boolean,\n'
        '  "is_in_repair": boolean,\n'
        '  "is_passenger_train": boolean,\n'
        '  "is_consolidated": boolean,\n'
        '  "escort_count": integer or 0,\n'
        '  "has_teplushka": boolean,\n'
        '  "teplushka_type": "freight_sps / freight_mps / passenger_sps / passenger_mps or null",\n'
        '  "is_asco_ferry": boolean,\n'
        '  "wagon_length_meters": float or null\n'
        "}\n\n"
        "Return ONLY a valid JSON object. UI language context: " + target_lang + ".\n"
    )

    audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

    response = client.models.generate_content(
        model="gemini-3.6-flash",
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
    if "is_asco_ferry" not in result or result["is_asco_ferry"] is None:
        result["is_asco_ferry"] = False
    if "wagon_length_meters" not in result:
        result["wagon_length_meters"] = None

    ferry_keywords = ["quruq", "kuryk", "курык", "aqtau", "aktau", "актау", "türkmenbaşı", "turkmenbashi", "туркменбаши", "trk", "трк", "bərə", "паром", "ferry"]
    spoken_text = str(result.get("transcript") or "").lower()
    if any(k in spoken_text for k in ferry_keywords):
        result["is_asco_ferry"] = True

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

    if nlu_data.get("is_asco_ferry"):
        gng = str(nlu_data.get("gng_code") or "")
        is_fixed_oil = any(gng.startswith(prefix) for prefix in ["2709", "2710", "2712", "2713"])
        
        if not is_fixed_oil and not nlu_data.get("wagon_length_meters"):
            msg = (
                "⚠️ Məlumat yoxdur: Bərə daşıması üçün vaqonun uzunluğu (metr) qeyd olunmalıdır (məsələn: 15m, 17m, 19m, 22m)."
                if lang == "AZ" else
                "⚠️ Отсутствует длина вагона: Для расчета паромной переправы необходимо обязательно указать длину вагона в метрах (например: 15м, 17м, 19м, 22м)."
            )
            missing.append(msg)
        
    return missing
