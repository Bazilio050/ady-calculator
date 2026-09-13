# Фиксированная ставка за паром в Аляте
FERRY_HANDLING_FEE_USD = 70.0

def calculate_ferry_fees(route_from: str, route_to: str, num_wagons: int = 1) -> dict:
    from_st = route_from.strip().lower()
    to_st = route_to.strip().lower()
    
    sea_terminals = ["курык", "актау", "трк", "туркменбаши"]
    
    nakat_fee = 0.0
    vykat_fee = 0.0

    if to_st in sea_terminals or to_st == "алят-эксп.":
        if from_st not in sea_terminals and from_st != "алят-эксп.":
            nakat_fee = FERRY_HANDLING_FEE_USD * num_wagons

    if from_st in sea_terminals:
        if to_st not in sea_terminals:
            vykat_fee = FERRY_HANDLING_FEE_USD * num_wagons

    return {
        "nakat_usd": nakat_fee,
        "vykat_usd": vykat_fee,
        "total_ferry_usd": nakat_fee + vykat_fee
    }

def test_ferry_fees_on_control_routes():
    """Автоматическая проверка наката и выката"""
    test_cases = [
        ("Беюк Кясик", "Алят-эксп.", 70.0, 0.0),   # Накат 70, Выкат 0
        ("ТРК", "Ялама", 0.0, 70.0),              # Накат 0, Выкат 70
        ("Сальяны", "Курык", 70.0, 0.0),           # Накат 70, Выкат 0
        ("Ялама", "Астара", 0.0, 0.0)              # Сухопутный: 0 и 0
    ]
    
    for from_st, to_st, exp_nakat, exp_vykat in test_cases:
        res = calculate_ferry_fees(from_st, to_st, num_wagons=1)
        assert res["nakat_usd"] == exp_nakat
        assert res["vykat_usd"] == exp_vykat

def test_ferry_fees_calculation():
    """Автоматическая проверка начисления сборов $70 USD за накат/выкат в Аляте"""
    from core.calculator import TariffCalculator

    # 1. Беюк Кясик -> Алят-эксп. (Накат: $70, Выкат: $0)
    res_1 = TariffCalculator.calculate_ferry_fees("Беюк Кясик", "Алят-эксп.")
    assert res_1["ferry_nakat_fee_usd"] == 70.0
    assert res_1["ferry_vykat_fee_usd"] == 0.0

    # 2. ТРК -> Ялама (Накат: $0, Выкат: $70)
    res_2 = TariffCalculator.calculate_ferry_fees("ТРК", "Ялама")
    assert res_2["ferry_nakat_fee_usd"] == 0.0
    assert res_2["ferry_vykat_fee_usd"] == 70.0

    # 3. Сальяны -> Курык (Накат: $70, Выкат: $0)
    res_3 = TariffCalculator.calculate_ferry_fees("Сальяны", "Курык")
    assert res_3["ferry_nakat_fee_usd"] == 70.0
    assert res_3["ferry_vykat_fee_usd"] == 0.0

    # 4. Ялама -> Астара (Сухопутный transit, сборы = $0)
    res_4 = TariffCalculator.calculate_ferry_fees("Ялама", "Астара")
    assert res_4["ferry_nakat_fee_usd"] == 0.0
    assert res_4["ferry_vykat_fee_usd"] == 0.0
