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
You are an expert railway & Caspian ferry freight NLU assistant for Azerbaijan Railways (ADY) and ASCO.
Analyze the user text query containing a freight shipment request.

ACTIVE RAILWAY TERMINOLOGY & VOCABULARY REFERENCE:
{rail_vocab}

Extract parameters into a JSON object matching the schema below.

CRITICAL RULES FOR GNG, CARGO NAME & WAGON TYPE:
- ALWAYS extract any cargo numeric code into 'gng_code' (e.g. if query contains "1001" or "GNG 1001", set 'gng_code': "1001").
- NEVER put text descriptions or wagon terms into 'gng_code'! Keep 'gng_code' STRICTLY NUMERIC.
- STRICT PRIORITY RULE FOR GNG: The abbreviation 'GNG', 'NHM' or 'ГНГ' followed by numbers represents strictly a cargo nomenclature code. It is STRICTLY FORBIDDEN to interpret 'GNG' as the city of Ganja (Gəncə) or any other similar-sounding word.
- TERMS LIKE 'qapalı vaqon', 'крытый вагон', 'полувагон', 'платформа', 'цистерна', 'çən', 'cistern' ARE WAGON TYPES ('wagon_type'), NEVER CARGO NAMES ('gng_name')!
- If GNG 1001 is provided without an explicit cargo description, set 'gng_name': "Buğda".
- Station ESR codes: Yalama=545006, Abşeron=548004, Biləcəri=546808, Böyük Kəsik=558701, Astara=554109, Ələt (Bərə/Паром)=549204.

CRITICAL RULES FOR CASPIAN FERRY PORTS & ROUTE SEPARATION:
- NEVER assign ferry ports ("Kuryk", "Aktau", "Turkmenbashi") to origin_name or origin_esr.
- Origin station is the entry border/station (e.g. "Böyük Kəsik" -> origin_esr: "558701", "Yalama" -> origin_esr: "545006").
- If the request mentions Caspian ferry ports, bind them STRICTLY to 'dest_name' & 'dest_esr':
  * "Quruq", "Kuryk", "Курык" -> dest_name: "Ələt eksport-Kurik", dest_esr: "553002"
  * "Aqtau", "Aktau", "Актау" -> dest_name: "Ələt eksport-Aktau", dest_esr: "549204"
  * "Türkmenbaşı", "Turkmenbashi", "Туркменбаши", "TRK", "ТРК" -> dest_name: "Ələt eksport-Türk.", dest_esr: "548803"
- Set 'is_asco_ferry': true if any ferry crossing or Caspian sea port is mentioned.
- Extract wagon length in meters into 'wagon_length_meters' as a float (e.g. "15m", "17 м", "16.97m" -> 15.0, 17.0, 16.97). If not explicitly mentioned, set 'wagon_length_meters': null.

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
  "teplushka_type": "freight_sps / freight_mps / passenger_sps / passenger_mps or null",
  "is_asco_ferry": boolean,
  "wagon_length_meters": float or null
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
    result["user_input_raw"] = user_input

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

    prompt = f"""
You are an expert railway & Caspian ferry freight NLU assistant for Azerbaijan Railways (ADY) and ASCO.
Listen carefully to the audio input containing a freight shipment request.

ACTIVE RAILWAY TERMINOLOGY & VOCABULARY REFERENCE:
{rail_vocab}

Tasks:
1. Transcribe the spoken text accurately into the 'transcript' field.
2. Extract shipment parameters into a JSON object matching the schema below.

CRITICAL RULES FOR GNG, CARGO NAME & WAGON TYPE:
- ALWAYS extract any spoken cargo numeric code into 'gng_code' (e.g. if user says "1001" or "GNG 1001", set 'gng_code': "1001"). Never put text descriptions into 'gng_code'!
- STRICT PRIORITY RULE FOR GNG: Spoken 'GNG', 'NHM' or 'ГНГ' followed by numbers represents strictly a cargo nomenclature code. It is STRICTLY FORBIDDEN to interpret 'GNG' as the city of Ganja (Gəncə) or any other similar-sounding word.
- TERMS LIKE 'qapalı vaqon', 'крытый вагон', 'полувагон', 'платформа', 'цистерна', 'çən', 'cistern' ARE WAGON TYPES ('wagon_type'), NEVER CARGO NAMES ('gng_name')!
- If GNG 1001 is provided without an explicit cargo description, set 'gng_name': "Buğda".
- Station ESR codes: Yalama=545006, Abşeron=548004, Biləcəri=546808, Böyük Kəsik=558701, Astara=554109, Ələt (Bərə/Паром)=549204.

CRITICAL RULES FOR CASPIAN FERRY PORTS & DESTINATION STATIONS:
- If spoken text mentions Caspian ferry ports, bind them strictly to the corresponding Alat ferry ESR station codes as dest_name & dest_esr:
  * "Quruq", "Kuryk", "Курык" -> dest_name: "Ələt eksport-Kurik", dest_esr: "553002"
  * "Aqtau", "Aktau", "Актау" -> dest_name: "Ələt eksport-Aktau", dest_esr: "549204"
  * "Türkmenbaşı", "Turkmenbashi", "Туркменбаши", "TRK", "ТРК" -> dest_name: "Ələt eksport-Türk.", dest_esr: "548803"
- Set 'is_asco_ferry': true if any ferry crossing or Caspian sea port is mentioned.
- Extract wagon length in meters into 'wagon_length_meters' as a float (e.g. "15m", "17 м", "16.97m" -> 15.0, 17.0, 16.97). If not explicitly mentioned, set 'wagon_length_meters': null.

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
  "explicit_mode": "import / export / transit or null",
  "is_empty": boolean,
  "axles_count": integer or null,
  "is_own_axles": boolean,
  "is_in_repair": boolean,
  "is_passenger_train": boolean,
  "is_consolidated": boolean,
  "escort_count": integer or 0,
  "has_teplushka": boolean,
  "teplushka_type": "freight_sps / freight_mps / passenger_sps / passenger_mps or null",
  "is_asco_ferry": boolean,
  "wagon_length_meters": float or null
}}

Return ONLY a valid JSON object. UI language context: {target_lang}.
"""

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
    result["user_input_raw"] = result.get("transcript", "")

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
    Проверяет данные, принудительно разделяет станции и предотвращает совпадение origin == dest.
    """
    missing = []
    input_text = str(nlu_data.get("user_input_raw") or "").lower()

    # 1. Гибкий поиск станции отправления (Origin) через регулярные выражения
    if re.search(r'б[её]юк\s+к[аяе]сик|beyuk\s*kasik|boyuk\s*kesik', input_text):
        nlu_data["origin_name"] = "Böyük Kəsik"
        nlu_data["origin_esr"] = "558701"
    elif "yalama" in input_text:
        nlu_data["origin_name"] = "Yalama"
        nlu_data["origin_esr"] = "545006"
    elif "astara" in input_text:
        nlu_data["origin_name"] = "Astara"
        nlu_data["origin_esr"] = "554109"

    # 2. Определение порта назначения (Dest)
    if any(k in input_text for k in ["kuryk", "kurik", "quruq", "курык"]):
        nlu_data["dest_name"] = "Ələt eksport-Kurik"
        nlu_data["dest_esr"] = "553002"
        nlu_data["is_asco_ferry"] = True
    elif any(k in input_text for k in ["aktau", "aqtau", "актау"]):
        nlu_data["dest_name"] = "Ələt eksport-Aktau"
        nlu_data["dest_esr"] = "549204"
        nlu_data["is_asco_ferry"] = True
    elif any(k in input_text for k in ["turkmenbashi", "türkmenbaşı", "туркменбаши", "trk", "трк"]):
        nlu_data["dest_name"] = "Ələt eksport-Türk."
        nlu_data["dest_esr"] = "548803"
        nlu_data["is_asco_ferry"] = True

    # 3. Страховка: Если origin и dest совпали, сбрасываем origin на реальную входную станцию
    if nlu_data.get("origin_esr") == nlu_data.get("dest_esr"):
        if re.search(r'б[её]юк\s+к[аяе]сик|beyuk|boyuk', input_text):
            nlu_data["origin_name"] = "Böyük Kəsik"
            nlu_data["origin_esr"] = "558701"
        elif "yalama" in input_text:
            nlu_data["origin_name"] = "Yalama"
            nlu_data["origin_esr"] = "545006"

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
