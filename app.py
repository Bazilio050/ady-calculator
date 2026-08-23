# ВЫВОД РЕЗУЛЬТАТОВ РАСЧЕТА (В ТОЧНОСТИ КАК НА СКРИНШОТЕ)
elif st.session_state.calc_result:
    data = st.session_state.calc_result
    st.success(t["success"].format(selected_year))
    
    with st.expander(t["json_expander"]):
        st.json(st.session_state.nlu_res)

    p1, p2, p3 = data["part1"], data["part2"], data["part3"]
    
    # 📍 1. Marşrut və daşıma şərtləri
    st.markdown(f"#### 📍 {t['sec1_title']}")
    st.markdown(
        f"| {t['col_param']} | {t['col_val']} |\n"
        f"| :--- | :--- |\n"
        f"| **{t['lbl_route']}** | {p1['route']} |\n"
        f"| **{t['lbl_type']}** | {p1['shipment_type']} |\n"
        f"| **{t['lbl_dist']}** | {p1['distance']} |\n"
        f"| **{t['lbl_cargo']}** | {p1['cargo_and_wagon']} |\n"
        f"| **{t['lbl_weight']}** | {p1['weight_info']} |\n"
        f"| **{t['lbl_period']}** | {p1['period']} |"
    )

    # ⚙️ 2. Əmsallar və valyuta məzənnəsi
    st.markdown(f"#### ⚙️ {t['sec2_title']}")
    t2_rows = [
        f"| **{t['lbl_exchange']}** | {p2['exchange_rate']} |", 
        f"| **{t['lbl_base_rate']}** | {p2['base_tariff']} |"
    ]
    for coeff in p2.get("coefficients", []):
        t2_rows.append(f"| **{coeff['name']}** | {coeff['value']} |")
    st.markdown(f"| {t['col_param']} | {t['col_val']} |\n| :--- | :--- |\n" + "\n".join(t2_rows))

    # 📐 3. Tarifin hesablanması
    st.markdown(f"#### 📐 {t['sec3_title']}")
    st.code(p3["formula"], language="text")
    
    table_rows = [
        f"| **{t['lbl_net_rate']}** | **{p3['net_ady_rate']}** |"
    ]

    st.markdown(
        f"| {t['col_rate_type']} | {t['col_amount']} |\n"
        f"| :--- | :--- |\n" +
        "\n".join(table_rows)
    )

    # Сноски и примечания
    if p3.get("notes"):
        st.markdown(f"**{t['notes_title']}**")
        for idx, note in enumerate(p3["notes"], start=1):
            if note:
                st.markdown(f"{idx}. *{note}*")
