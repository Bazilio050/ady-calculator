import json
from google.genai import types

def call_gemini_nlu(client, user_input_text, lang):
    lang_map = {"AZ": "Azerbaijani", "RU": "Russian", "EN": "English"}
    target_lang = lang_map.get(lang, "Azerbaijani")

    prompt = (
        "You are an expert railway logistics NLU parser for Azerbaijan Railways (ADY).\n"
        "Extract shipment parameters from text into JSON. Return ONLY clean JSON:\n"
        "{\n"
        '  "route_from": "string or null (OFFICIAL ADY station name normalized to Latin, e.g. Yalama, Bileceri, Boyuk Kesik, Alat, Astara, Culfa, Absheron, Xudat)",\n'
        '  "route_to": "string or null (OFFICIAL ADY station name normalized to Latin, e.g. Yalama, Bileceri, Boyuk Kesik, Alat, Astara, Culfa, Absheron, Xudat)",\n'
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
        "STRICT ROUTE RULES:\n"
        "- NEVER set 'route_from' and 'route_to' to the same station if two distinct stations are mentioned.\n"
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
