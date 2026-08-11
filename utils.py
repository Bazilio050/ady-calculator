BORDER_STATION_ESR_OVERRIDE = {
    "boyuk kesik": "558701",  # Böyük Kəsik (eksport)
    "yalama": "547508",       # Yalama (eksport) -> даёт точные 680 км!
    "astara": "554109",       # Astara (eksport)
    "culfa": "550004",        # Culfa (eksport)
    "serur": "550409"         # Şərur (eksport)
}

def resolve_esr_by_station_name(station_name: str) -> str:
    """
    Сканирует Distances.txt и возвращает точный 6-значный ЕСР по названию станции.
    Для пограничных станций приоритет отдаётся экспортным кодам.
    """
    if not station_name:
        return ""

    # Очищаем название от суффиксов и спецсимволов
    clean = re.sub(r'-(eksp|эксп|exp)\b', '', str(station_name), flags=re.IGNORECASE).strip().lower()
    clean_norm = clean.replace('ö', 'o').replace('ə', 'e').replace('ı', 'i').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')

    # 1. Приоритетный поиск для погранпереходов
    for b_name, b_esr in BORDER_STATION_ESR_OVERRIDE.items():
        if b_name in clean_norm or clean_norm in b_name:
            return b_esr

    # 2. Сканирование Distances.txt для остальных станций
    possible_paths = ["Distances.txt", "tariff_data/Distances.txt", "data/Distances.txt", "tables/Distances.txt"]
    dist_file = next((p for p in possible_paths if os.path.exists(p)), None)

    if not dist_file:
        return ""

    try:
        with open(dist_file, "r", encoding="utf-8") as f:
            for line in f:
                if "|" not in line or ":---" in line or "Stansiyanın" in line:
                    continue

                parts = [p.strip() for p in line.split("|")]
                if len(parts) < 3:
                    continue

                file_st_name = parts[1].replace("*", "").strip().lower()
                file_st_name = file_st_name.replace('ö', 'o').replace('ə', 'e').replace('ı', 'i').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')
                file_esr = re.sub(r'\D', '', parts[2])

                if clean_norm and file_st_name and (clean_norm in file_st_name or file_st_name in clean_norm):
                    return file_esr
    except Exception as e:
        print(f"Error resolving ESR: {e}")

    return ""
