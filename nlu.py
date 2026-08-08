import json
from google.genai import types

def call_gemini_nlu(client, user_input_text, lang):
    lang_map = {"AZ": "Azerbaijani", "RU": "Russian", "EN": "English"}
    target_lang = lang_map.get(lang, "Azerbaijani")

    prompt = (
        "You are an expert railway logistics NLU parser for Azerbaijan Railways (ADY).\n"
        "Extract shipment parameters from text into JSON. Return ONLY clean JSON:\n"
        "{\n"
        '  "route_from": "string or null (OFFICIAL ADY station name normalized to Latin, e.g. Yalama, Bileceri, Boyuk Kesik, Alat, Astara, Culfa, Absheron)",\n'
        '  "route_to": "string or null (OFFICIAL ADY station name normalized to Latin, e.g. Yalama, Bileceri, Boyuk Kesik, Alat, Astara, Culfa, Absheron)",\n'
        '  "cargo_gng_code": "string or null (extract 2-to-8 digit GNG/NHM code, e.g. 72, 4407, 0207)",\n'
        f'  "cargo_name": "string or null (Short official commodity name translated STRICTLY to {target_lang} in 1-3 words based on GNG code or input text)",\n'
        '  "actual_weight_tons": float or null,\n'
        '  "wagon_type": "string (universal/tank/ref/thermos/autocarrier/container)",\n'
        '  "park_type": "string (SPS/MPS)",\n'
        '  "ref_section_cargo_wagons": integer or null (Extract number of CARGO wagons in refrigerated section, e.g. "5+1" -> 5, "1+5" -> 5, "6+1" -> 6),\n'
        '  "is_tariff_agreement_origin": boolean,\n'
        '  "requested_period": "string or null",\n'
        '  "explicit_mode": "string or null (import/export/transit)"\n'
        "}\n\n"
        "STRICT STATION NORMALIZATION RULES:\n"
        "- Convert ANY station name (Russian, Azerbaijani, typos, slang, missing letters) directly into official ADY station Latin names:\n"
        "  * 'Баладжары' / 'Баладжар' / 'Baladjary' / 'Baladžary' -> 'Bileceri'\n"
        "  * 'Беюк-Кесик' / 'Б.Касик' / 'Беюк Кесик' / 'Boyukkasik' -> 'Boyuk Kesik'\n"
        "  * 'Ялама' -> 'Yalama'\n"
        "  * 'Алят' / 'Элет' -> 'Alat'\n"
        "  * 'Астара' -> 'Astara'\n"
        "  * 'Абшерон' -> 'Absheron'\n\n"
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
    if not gng and not cargo_name:
        missing_items.append("📦 **Yükün adı və ya GNG/NHM kodu** (Cargo code or name)" if lang == "AZ" else ("📦 **Наименование груза или код ГНГ/NHM**" if lang == "RU" else "📦 **Cargo name or GNG/NHM code**"))

    return missing_items
