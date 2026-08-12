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
        "- Do NOT confuse Biləcəri (546808) with ferry/port codes (547209).\n"
        "- GNG/NHM cargo codes can be 2, 4, or 8 digits (e.g., '78', '72', '0207', '27130000'). ALWAYS output them strictly as strings with leading zeros preserved.\n"
        "- If a 2-digit group code is provided (like '78' or '72'), set 'gng_code' to string (e.g., \"78\") AND infer the cargo group name for 'gng_name' (e.g., \"Svinç / Əlvan metallar\").\n\n"
        "EXPECTED JSON STRUCTURE:\n"
        "{\n"
        '  "origin_esr": "6-digit ESR string or null",\n'
        f'  "origin_name": "Station name in {target_lang}",\n'
        '  "dest_esr": "6-digit ESR string or null",\n'
        f'  "dest_name": "Station name in {target_lang}",\n'
        '  "gng_code": "2, 4, or 8 digit GNG code string or null",\n'
        f'  "gng_name": "Short cargo description in {target_lang}",\n'
        '  "weight_tons": float or null,\n'
        '  "wagon_type": "universal / tank / ref / thermos / autocarrier",\n'
        '  "park_type": "SPS / MPS",\n'
        '  "ref_section_cargo_wagons": integer or null,\n'
        '  "explicit_mode": "import / export / transit or null"\n'
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
    return result


def validate_nlu_input(nlu_res, lang="AZ"):
    """
    Проверяет наличие минимально необходимых данных для расчёта.
    """
    missing_items = []

    st_from = nlu_res.get("origin_esr") or nlu_res.get("origin_name")
    st_to = nlu_res.get("dest_esr") or nlu_res.get("dest_name")
    weight = nlu_res.get("weight_tons")
    gng = nlu_res.get("gng_code")
    cargo_name = nlu_res.get("gng_name")

    lang_upper = str(lang).upper()

    if not st_from:
        missing_items.append(
            "📍 **Başlanğıc stansiyası**" if lang_upper == "AZ" else ("📍 **Станция отправления**" if lang_upper == "RU" else "📍 **Origin station**")
        )
    if not st_to:
        missing_items.append(
            "📍 **Təyinat stansiyası**" if lang_upper == "AZ" else ("📍 **Станция назначения**" if lang_upper == "RU" else "📍 **Destination station**")
        )
    if not weight or float(weight) <= 0:
        missing_items.append(
            "⚖️ **Faktiki çəki (tonla)**" if lang_upper == "AZ" else ("⚖️ **Фактический вес (в тоннах)**" if lang_upper == "RU" else "⚖️ **Actual weight in tons**")
        )

    gng_str = str(gng).strip() if gng is not None else ""
    cargo_str = str(cargo_name).strip() if cargo_name is not None else ""

    if not gng_str and not cargo_str:
        missing_items.append(
            "📦 **Yükün adı və ya GNG/NHM kodu**" if lang_upper == "AZ" else ("📦 **Наименование груза или код ГНГ/NHM**" if lang_upper == "RU" else "📦 **Cargo name or GNG/NHM code**")
        )

    return missing_items
