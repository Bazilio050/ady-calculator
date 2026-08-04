# Внутри load_selective_context:
    if any(k in query_lower for k in ["tranzit", "транзит", "transit"]):
        # Если в запросе транзит — СТРОГО подгружаем Таблицу 4
        for f_name in ["Table_4_Tariffs.txt", "Table4.txt", "Cədvəl4.txt"]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)
                break
    elif any(
        k in query_lower
        for k in [
            "цистерн",
            "çən",
            "tank",
            "нефть",
            "neft",
            "газ",
            "qaz",
            "масло",
            "спирт",
            "2709",
            "2710",
        ]
    ):
        for f_name in [
            "Table_6_Tariffs.txt",
            "Table_6_Tanks.txt",
            "Table6.txt",
            "Cədvəl6.txt",
        ]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)
                break
    # ... остальные проверки ...
    else:
        # По умолчанию подгружаем Таблицу 3
        for f_name in ["Table_3_Tariffs.txt", "Table3.txt", "Cədvəl3.txt"]:
            if os.path.exists(f_name):
                files_to_load.append(f_name)
                break
