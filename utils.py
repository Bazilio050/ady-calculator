import json
import os
import re
import streamlit as st

@st.cache_data(show_spinner=False)
def load_rules_config():
    if os.path.exists("rules_config.json"):
        with open("rules_config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def normalize_st_name(name):
    if not name:
        return ""
    n = name.lower().strip()
    n = re.sub(r'[\*\_\#]', '', n)
    n = re.sub(r'[\(\-–\s]*(eksport|eksp|эксп|exp|eks)[\)\.\s]*', '', n)
    
    n = n.replace('баладжары', 'bileceri').replace('baladzary', 'bileceri').replace('baladzhary', 'bileceri').replace('baladžary', 'bileceri')
    n = n.replace('беюк', 'boyuk').replace('кесик', 'kesik').replace('касик', 'kesik')
    n = n.replace('ялама', 'yalama').replace('астара', 'astara').replace('алят', 'alat')
    n = n.replace('джульфа', 'culfa').replace('абшерон', 'absheron').replace('баку', 'baki')
    n = n.replace('ə', 'e').replace('ö', 'o').replace('ü', 'u').replace('ı', 'i').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')
    n = n.replace('beyuk', 'boyuk').replace('kasik', 'kesik').replace('elet', 'alat')
    return re.sub(r'[^a-z0-9]', '', n)

@st.cache_data(show_spinner=False)
def load_distances_map():
    dist_map = {}
    dist_files = ["Distances.txt", "Məsafə.txt", "Masafe.txt", "Distance.txt"]
    target_file = next((df for df in dist_files if os.path.exists(df)), None)
    
    if target_file:
        with open(target_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        header_cols = []
        for line in lines:
            if "|" in line and "stansiyanın adı" in line.lower():
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 3:
                    header_cols = [normalize_st_name(p) for p in parts[2:]]
                continue
            
            if "|" in line and header_cols and not line.startswith("| :---") and not line.startswith("#"):
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 3:
                    row_st = normalize_st_name(parts[0])
                    val_parts = parts[2:]
                    for i, val_str in enumerate(val_parts):
                        if i < len(header_cols):
                            digits = re.sub(r'[^\d]', '', val_str)
                            if digits:
                                km = int(digits)
                                col_st = header_cols[i]
                                if row_st and col_st:
                                    dist_map[(row_st, col_st)] = km
                                    dist_map[(col_st, row_st)] = km
    return dist_map

def find_distance_in_memory(st_from, st_to):
    dist_map = load_distances_map()
    s1 = normalize_st_name(st_from)
    s2 = normalize_st_name(st_to)

    if (s1, s2) in dist_map:
        return dist_map[(s1, s2)]
    if (s2, s1) in dist_map:
        return dist_map[(s2, s1)]

    fallback_map = {
        ("yalama", "boyukkesik"): 680,
        ("boyukkesik", "yalama"): 680,
        ("yalama", "astara"): 504,
        ("astara", "yalama"): 504,
        ("boyukkesik", "astara"): 586,
        ("astara", "boyukkesik"): 586,
        ("yalama", "alat"): 271,
        ("boyukkesik", "alat"): 429,
        ("absheron", "boyukkesik"): 476,
        ("absheron", "yalama"): 204,
        ("yalama", "bileceri"): 192,
        ("bileceri", "yalama"): 192
    }

    if (s1, s2) in fallback_map:
        return fallback_map[(s1, s2)]
    if (s2, s1) in fallback_map:
        return fallback_map[(s2, s1)]

    return None
