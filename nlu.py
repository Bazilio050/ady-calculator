import json
from google.genai import types

def call_gemini_nlu(client, user_input_text, lang):
    lang_map = {"AZ": "Azerbaijani", "RU": "Russian", "EN": "English"}
    target_lang = lang_map.get(lang, "Azerbaijani")

    prompt = (
        "You are an expert railway logistics NLU parser for Azerbaijan Railways (ADY).\n"
        "Extract shipment parameters from text into JSON. Return ONLY clean JSON:\n"
        "{\n"
        '  "route_from": "string or null (OFFICIAL ADY station name normalized to Latin, e.g. Yalama, Sumqayit, Bileceri, Boyuk Kesik, Alat, Astara, Culfa, Absheron, Xudat)",\n'
        '  "route_to": "string or null (OFFICIAL ADY station name normalized to Latin, e.g. Yalama, Sumqayit, Bileceri, Boyuk Kesik, Alat, Astara, Culfa, Absheron, Xudat)",\n'
        '  "cargo_gng_code": "string or null (Extract ANY 2-digit, 4-digit, or 6-to-8 digit numeric code representing GNG/NHM, e.g. 72, 28, 2815, 4407, 0207)",\n'
        f'  "cargo_name": "string or null (Short official commodity name translated STRICTLY to {target_lang} in 1-3 words based on GNG code or input text. If only GNG code like 2815 or 72 is provided, provide generic name for this GNG category)",\n'
        '  "actual_weight_tons": float or null,\n'
        '  "wagon_type": "string (universal/tank/ref/thermos/autocarrier/container)",\n'
        '  "park_type": "string (SPS/MPS)",\n'
        '  "ref_section_cargo_wagons": integer or null (Extract number of CARGO wagons in refrigerated section, e.g. "5+1" -> 5, "1+5" -> 5, "6+1" -> 6),\n'
        '  "is_tariff_agreement_origin": boolean,\n'
        '  "requested_period": "string or null",\n'
        '  "explicit_mode": "string or null (import/export/transit)"\n'
        "}\n\n"
        "CRITICAL CARGO RULES:\n"
        "- ANY standalone 2-digit (e.g. 72, 28), 4-digit (e.g. 2815) or 8-digit numbers MUST be extracted as 'cargo_gng_code' unless explicitly specified as weight in tons.\n"
        "- If user enters '2815', set 'cargo_gng_code' to '2815'.\n\n"
        "STRICT ROUTE RULES:\n"
        "- NEVER set 'route_from' and 'route_to' to the same station if two distinct stations are mentioned.\n"
        "- 'сумгаит' / 'sumqait' / 'sumgayit' -> 'Sumqayit'\n"
        "- 'худат' / 'xudat' -> 'Xudat'\n"
        "- 'ялама' / 'yalama' -> 'Yalama'\n\n"
        f"USER INPUT:\n{user_input_text}"
    )
    
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
        ),
    )

    raw_text = response.text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]

    return json.loads(raw_text.strip())

def validate_nlu_input(nlu_res, lang):
    missing_items = []
    
    st_from = nlu_res.get("route_from")
    st_to = nlu_res.get("route_to")
    weight = nlu_res.get("actual_weight_tons")
    gng = nlu_res.get("cargo_gng_code")
    cargo_name = nlu_res.get("cargo_name")

    if not st_from:
        missing_items.append("📍 **Başlanğıc stansiyası** (Origin station)" if lang == "AZ" else ("📍 **Станция отправления**" if lang == "RU" else "📍 **Origin station**"))
    if not st_to:
        missing_items.append("📍 **Təyinat stansiyası** (Destination station)" if lang == "AZ" else ("📍 **Станция назначения**" if lang == "RU" else "📍 **Destination station**"))
    if not weight or float(weight) <= 0:
        missing_items.append("⚖️ **Faktiki çəki (tonla)** (Weight in tons)" if lang == "AZ" else ("⚖️ **Фактический вес (в тоннах)**" if lang == "RU" else "⚖️ **Actual weight in tons**"))
    
    gng_str = str(gng).strip() if gng is not None else ""
    cargo_str = str(cargo_name).strip() if cargo_name is not None else ""
    
    if not gng_str and not cargo_str:
        missing_items.append("📦 **Yükün adı və ya GNG/NHM kodu** (Cargo code or name)" if lang == "AZ" else ("📦 **Наименование груза или код ГНГ/NHM**" if lang == "RU" else "📦 **Cargo name or GNG/NHM code**"))

    return missing_items
