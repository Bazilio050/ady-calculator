import json
from google.genai import types

def call_gemini_nlu(client, user_input_text, site_lang="AZ"):
    """
    Парсит пользовательский запрос и возвращает структурированный JSON с ЕСР-кодами,
    полными названиями станций и коротким именем груза на языке сайта (site_lang).
    Использует строго рабочую модель gemini-3.5-flash-lite.
    """
    lang_map = {"AZ": "Azerbaijani", "RU": "Russian", "EN": "English"}
    target_lang = lang_map.get(str(site_lang).upper(), "Azerbaijani")

    prompt = (
        "You are an expert railway logistics NLU parser for Azerbaijan Railways (ADY).\n"
        f"Parse user input into a strict JSON object. All station names ('origin_name', 'dest_name') "
        f"must be translated strictly to {target_lang}. Short cargo name ('gng_name') MUST be translated strictly to {target_lang} (1-3 words).\n\n"
        "EXPECTED JSON STRUCTURE:\n"
        "{\n"
        '  "origin_esr": "string or null (6-digit ESR station code, e.g. 545006, 558701, 548004)",\n'
        f'  "origin_name": "string or null (Official full station name in {target_lang})",\n'
        '  "dest_esr": "string or null (6-digit ESR station code, e.g. 545006, 558701, 548004)",\n'
        f'  "dest_name": "string or null (Official full station name in {target_lang})",\n'
        '  "gng_code": "string or null (Extract numeric GNG/NHM cargo code: 2, 4, 6 or 8 digits, e.g. 2701, 72, 2815)",\n'
        f'  "gng_name": "string or null (Short 1-3 words cargo description strictly in {target_lang})",\n'
        '  "weight_tons": float or null,\n'
        '  "wagon_type": "string (universal / tank / ref / thermos / autocarrier / container)",\n'
        '  "park_type": "string (SPS / MPS)",\n'
        '  "ref_section_cargo_wagons": integer or null (e.g. 5 for 5+1),\n'
        '  "explicit_mode": "string or null (import / export / transit)"\n'
        "}\n\n"
        "CRITICAL ESR & STATION RULES:\n"
        "- Yalama -> ESR: 545006\n"
        "- Böyük Kəsik / Beyuk Kasik -> ESR: 558701\n"
        "- Abşeron / Absheron / Апшерон -> ESR: 548004\n"
        "- Bakı-Yük / Баку-Товарная -> ESR: 547105\n"
        "- Astara -> ESR: 554109\n"
        "- Culfa / Джульфа -> ESR: 550004\n"
        "- Ələt / Alat / Kurik / Kuryk / Aktau / TRK:\n"
        "  * If mode is import/export (local station) -> ESR: 548703 (Ələt yeni)\n"
        "  * Otherwise (default border/ferry transition) -> ESR: 549204 (Ələt eksport Aktau)\n"
        "- IF BOTH STATIONS ARE BORDER CROSSINGS (e.g. Yalama & Böyük Kəsik) -> set 'explicit_mode' to 'transit'.\n\n"
        f"USER INPUT:\n{user_input_text}"
    )

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",  # СТРОГО gemini-3.5-flash-lite
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
