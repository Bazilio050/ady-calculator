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
    raw_norm = normalize_simple(raw_text)

    # Словари ключевых слов
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

    # 1. Жестко ищем портовые ключевые слова по всему сырому тексту
    found_port = None
    for kw, target_st in port_map.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', raw_norm) or kw in raw_norm:
            found_port = target_st
            break

    # 2. Определяем позицию порта в тексте (начало или конец)
    first_word = raw_norm.split()[0] if raw_norm.split() else ""
    is_port_start = any(kw in first_word for kw in port_map.keys())

    if is_port_start:
        res["from_station"] = found_port
        # Если назначение не заполнено, берем следующее слово (например, "Сальяны")
        words = [w for w in raw_text.split() if w.lower() not in ["4407", "крытый", "35т", "спс", "вагон"]]
        if len(words) > 1 and not res.get("to_station"):
            res["to_station"] = words[1].title()
    elif found_port:
        res["to_station"] = found_port
        # Если отправление не заполнено, берём первое слово (например, "Апшерон")
        words = raw_text.split()
        if words and not res.get("from_station"):
            res["from_station"] = words[0].title()

    # 3. Базовая подстраховка для NLU
    if not res.get("from_station") and raw_text.split():
        res["from_station"] = raw_text.split()[0].title()

    # 4. Определение вида перевозки
    norm_from = normalize_simple(res.get("from_station", ""))
    norm_to = normalize_simple(res.get("to_station", ""))

    is_from_border = any(b in norm_from for b in border_keywords)
    is_from_port = "elet" in norm_from or "alat" in norm_from or "liman" in norm_from
    is_to_border = any(b in norm_to for b in border_keywords)
    is_to_port = "elet" in norm_to or "alat" in norm_to or "liman" in norm_to

    if (is_from_border or is_from_port) and (is_to_border or is_to_port):
        res["shipment_type"] = "transit"
    elif (is_from_border or is_from_port) and not (is_to_border or is_to_port):
        res["shipment_type"] = "import"
    elif not (is_from_border or is_from_port) and (is_to_border or is_to_port):
        res["shipment_type"] = "export"
    else:
        res["shipment_type"] = "local"

    return res
