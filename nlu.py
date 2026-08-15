import json
from google.genai import types

def call_gemini_nlu(client, user_input_text, site_lang="AZ"):
    lang_map = {"AZ": "Azerbaijani", "RU": "Russian", "EN": "English"}
    target_lang = lang_map.get(str(site_lang).upper(), "Azerbaijani")

    prompt = (
        "You are an expert railway logistics NLU parser for Azerbaijan Railways (ADY).\n"
        f"Parse user input into a strict JSON object. Translate station names ('origin_name', 'dest_name') "
        f"and short cargo name ('gng_name') STRICTLY to {target_lang}.\n\n"
        "CRITICAL ESR CODE & GNG INSTRUCTIONS:\n"
        "- Always output the exact standard 6-digit ESR code for each station ('origin_esr', 'dest_esr').\n"
        "- Example ESRs: Yalama=545006, Biləcəri/Баладжары=546808, Abşeron=548004, Böyük Kəsik=558701, Bakı-Yük=547105, Astara=554109.\n"
        "- GNG/NHM cargo codes can be any digit length from 2 to 8 digits (e.g., '78', '72', '0207', '8601', '99220000'). ALWAYS output them strictly as strings with leading zeros preserved.\n\n"
        "SPECIAL SECTION 3.7, 3.8 & 3.9 INSTRUCTIONS:\n"
        "- Movement on own axles (öz oxları üzərində / на своих осях): set 'is_own_axles': true. Keywords: 'öz oxları', 'на своих осях', 'локомотив', 'кран', '8601'-'8606'.\n"
        "- Wagon going to/from repair (təmirə/təmirdən / в ремонт/из ремонта): set 'is_in_repair': true.\n"
        "- Moving within passenger train (sərnişin qatarı / пассажирский поезд): set 'is_passenger_train': true.\n"
        "- Consolidated cargo (yığma göndərmə / сборный груз): set 'is_consolidated': true.\n"
        "- Section 3.9 Escort / Attendants (bələdçi / проводник / водитель): extract integer 'escort_count' (default 0).\n"
        "- Section 3.9 Teplushka / Escort wagon (tepluşka / теплушка / вагон сопровождения): set 'has_teplushka': true. Determine 'teplushka_type': 'freight_mps' (0.23 CHF/axle-km), 'freight_sps' (0.20 CHF/axle-km), 'passenger_mps' (0.35 CHF/axle-km), 'passenger_sps' (0.30 CHF/axle-km). Default to 'freight_sps'.\n\n"
        "EMPTY WAGON RUN INSTRUCTIONS:\n"
        "- Detect if user input indicates an empty wagon movement or return (keywords: 'boş', 'порожний', 'возврат', 'empty'). Set 'is_empty': true or false.\n"
        "- If 'is_empty' is true and no GNG code is provided, set 'gng_code': \"99220000\" and 'gng_name': \"Yükdən boşaldılmış vaqonlar\" (or translated equivalent).\n"
        "- For empty wagons, default 'park_type' to \"SPS\" and 'axles_count' to 4 unless specified otherwise.\n\n"
        "EXPECTED JSON STRUCTURE:\n"
        "{\n"
        '  "origin_esr": "6-digit ESR string or null",\n'
        f'  "origin_name": "Station name in {target_lang}",\n'
        '  "dest_esr": "6-digit ESR string or null",\n'
        f'  "dest_name": "Station name in {target_lang}",\n'
        '  "gng_code": "2, 4, or 8 digit GNG code string or null",\n'
        f'  "gng_name": "Short cargo description in {target_lang}",\n'
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
        '  "teplushka_type": "freight_sps / freight_mps / passenger_sps / passenger_mps or null"\n'
        "}\n\n"
        f"USER INPUT:\n{user_input_text}"
    )

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
        ),
        contents=prompt,
    )

    raw_text = response.text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]

    result = json.loads(raw_text.strip())
    result["site_lang"] = str(site_lang).upper()
    
    # Дефолтные значения для новых полей пункта 3.9
    if "escort_count" not in result or result["escort_count"] is None:
        result["escort_count"] = 0
    if "has_teplushka" not in result or result["has_teplushka"] is None:
        result["has_teplushka"] = False
    if "teplushka_type" not in result or not result["teplushka_type"]:
        result["teplushka_type"] = "freight_sps"

    # 💡 ПОДСТРАХОВКА: Проверка ключевых слов вручную
    input_lower = user_input_text.lower()
    if any(k in input_lower for k in ["boş", "порожн", "empty", "возврат", "qaytar"]):
        result["is_empty"] = True
    if any(k in input_lower for k in ["öz ox", "на своих осях", "своих осях", "локомотив", "кран"]):
        result["is_own_axles"] = True
    if any(k in input_lower for k in ["təmir", "ремонт", "repair"]):
        result["is_in_repair"] = True
    if any(k in input_lower for k in ["sərnişin qatar", "пассажирский поезд"]):
        result["is_passenger_train"] = True
    if any(k in input_lower for k in ["yığma", "сборный", "сборная", "consolidated"]):
        result["is_consolidated"] = True
    if any(k in input_lower for k in ["tepluşka", "теплушка", "вагон сопровождения"]):
        result["has_teplushka"] = True

    return result


def validate_nlu_input(nlu_res, lang="AZ"):
    """
    Проверяет наличие минимально необходимых данных для расчёта.
    """
    missing_items = []
    lang_upper = str(lang).upper()

    raw_is_empty = nlu_res.get("is_empty")
    is_empty = raw_is_empty.lower() in ["true", "1", "yes"] if isinstance(raw_is_empty, str) else bool(raw_is_empty)
    is_own_axles = bool(nlu_res.get("is_own_axles"))
    has_teplushka = bool(nlu_res.get("has_teplushka"))
    escort_count = int(nlu_res.get("escort_count", 0))

    if is_empty:
        if not nlu_res.get("gng_code"):
            nlu_res["gng_code"] = "99220000"
            nlu_res["gng_name"] = "Yükdən boşaldılmış vaqonlar" if lang_upper == "AZ" else ("Вагоны, очищенные после выгрузки" if lang_upper == "RU" else "Empty uncleaned/cleaned wagons")
        nlu_res["park_type"] = "SPS"
        if not nlu_res.get("axles_count"):
            nlu_res["axles_count"] = 4
        nlu_res["is_empty"] = True

    st_from = nlu_res.get("origin_esr") or nlu_res.get("origin_name")
    st_to = nlu_res.get("dest_esr") or nlu_res.get("dest_name")
    weight = nlu_res.get("weight_tons")
    gng = nlu_res.get("gng_code")
    cargo_name = nlu_res.get("gng_name")

    if not st_from:
        missing_items.append(
            "📍 **Başlanğıc stansiyası**" if lang_upper == "AZ" else ("📍 **Станция отправления**" if lang_upper == "RU" else "📍 **Origin station**")
        )
    if not st_to:
        missing_items.append(
            "📍 **Təyinat stansiyası**" if lang_upper == "AZ" else ("📍 **Станция назначения**" if lang_upper == "RU" else "📍 **Destination station**")
        )
    
    # Для порожнего пробега, движения на своих осях, проезда проводников или отдельно теплушки вес НЕ является обязательным полем
    if not is_empty and not is_own_axles and not has_teplushka and escort_count == 0 and (not weight or float(weight) <= 0):
        missing_items.append(
            "⚖️ **Faktiki çəki (tonla)**" if lang_upper == "AZ" else ("⚖️ **Фактический вес (в тоннах)**" if lang_upper == "RU" else "⚖️ **Actual weight in tons**")
        )

    gng_str = str(gng).strip() if gng is not None else ""
    cargo_str = str(cargo_name).strip() if cargo_name is not None else ""

    if not gng_str and not cargo_str and not is_own_axles and not has_teplushka and escort_count == 0:
        missing_items.append(
            "📦 **Yükün adı və ya GNG/NHM kodu**" if lang_upper == "AZ" else ("📦 **Наименование груза или код ГНГ/NHM**" if lang_upper == "RU" else "📦 **Cargo name or GNG/NHM code**")
        )

    return missing_items


def call_gemini_audio_nlu(client, audio_bytes: bytes, mime_type: str = "audio/wav", lang: str = "AZ") -> dict:
    """
    Принимает байты аудиозаписи, выполняет транскрибацию и NLU-анализ ж/д терминов 
    в один проход через модель Gemini.
    """
    prompt = f"""
    You are an expert railway freight NLU assistant for Azerbaijan Railways (ADY).
    Listen carefully to the audio input containing a freight shipment request (it can be in Russian, Azerbaijani, or English).

    Tasks:
    1. Transcribe the spoken text accurately into the 'transcript' field.
    2. Extract shipment entities according to the NLU schema:
       - 'transcript': Exact transcribed text spoken by user
       - 'origin_name': Departure station name
       - 'dest_name': Destination station name
       - 'weight_tons': Weight in metric tons (float)
       - 'gng_code': Cargo GNG/NHM code (keep leading zeros if present)
       - 'cargo_name': Name of cargo
       - 'wagon_type': Wagon type (universal, cistern, ref, container, platform, transporter, etc.)
       - 'park_type': 'SPS' or 'MPS'
       - 'is_empty': boolean (true if empty return/run)
       - 'is_own_axles': boolean (movement on own axles / locomotive / crane)
       - 'has_teplushka': boolean
       - 'escort_count': integer (count of attendants/conductors)
       - 'is_consolidated': boolean (sborny / yığma cargo)
       - 'explicit_mode': 'import', 'export', 'transit' or null

    Return ONLY a valid JSON object matching this schema. UI language context: {lang}.
    """

    audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[audio_part, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    return json.loads(response.text)
