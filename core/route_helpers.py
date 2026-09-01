# core/route_helpers.py
import re

def normalize_simple(text: str) -> str:
    if not text:
        return ""
    return str(text).lower().replace("ə", "e").replace("ö", "o").replace("ü", "u").replace("ç", "c").replace("ş", "s")

def normalize_nlu_stations(nlu_res: dict, raw_text: str = "") -> dict:
    if not isinstance(nlu_res, dict):
        nlu_res = {}

    res = nlu_res.copy()
    
    # Гарантируем, что значение всегда является строкой, а не None
    from_st = str(res.get("from_station") or "").strip()
    to_st = str(res.get("to_station") or "").strip()

    raw_norm = normalize_simple(raw_text)

    # Карта портов и терминалов
    port_map = {
        "trk": "Ələt-eksp.Türk.",
        "трк": "Ələt-eksp.Türk.",
        "туркмен": "Ələt-eksp.Türk.",
        "turkmen": "Ələt-eksp.Türk.",
        "aktau": "Ələt-eksp.Aktau",
        "актау": "Ələt-eksp.Aktau",
        "kurik": "Ələt-eksp.Kurik",
        "курык": "Ələt-eksp.Kurik"
    }

    border_keywords = ["yalama", "ялама", "boyuk kesik", "boyuk", "беюк", "кясик", "astara", "астара", "culfa", "джульфа"]

    # Ищем портовое ключевое слово в сыром тексте
    found_port = None
    for kw, target_st in port_map.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', raw_norm) or kw in raw_norm:
            found_port = target_st
            break

    words = raw_text.split()
    first_word = normalize_simple(words[0]) if words else ""
    is_port_start = any(kw in first_word for kw in port_map.keys())

    # 1. Если порт стоит ПЕРВЫМ словом (Импорт из порта)
    if is_port_start:
        res["from_station"] = found_port
        clean_words = [w for w in words if w.lower() not in ["4407", "крытый", "35т", "спс", "вагон"]]
        if len(clean_words) > 1 and not to_st:
            res["to_station"] = clean_words[1].title()

    # 2. Во всех остальных случаях (Экспорт в порт / Транзит через порт)
    elif found_port:
        res["to_station"] = found_port
        if words and not from_st:
            res["from_station"] = words[0].title()

    # 3. Резервная подстановка отправления
    if not res.get("from_station") and words:
        res["from_station"] = words[0].title()

    # 4. Определение вида перевозки
    norm_from = normalize_simple(res.get("from_station", ""))
    norm_to = normalize_simple(res.get("to_station", ""))

    is_from_border = any(b in norm_from for b in border_keywords) or "elet" in norm_from
    is_to_border = any(b in norm_to for b in border_keywords) or "elet" in norm_to

    if is_from_border and is_to_border:
        res["shipment_type"] = "transit"
    elif is_from_border and not is_to_border:
        res["shipment_type"] = "import"
    elif not is_from_border and is_to_border:
        res["shipment_type"] = "export"
    else:
        res["shipment_type"] = "local"

    return res
