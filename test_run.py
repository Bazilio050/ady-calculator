from engine import calculate_freight_tariff

# Имитируем входящие данные рейса
sample_nlu = {
    "origin_esr": "54890",   # Станция отправления
    "dest_esr": "55300",     # Станция назначения
    "gng_code": "271019",    # Нефтепродукты
    "weight_tons": 55,       # Вес
    "wagon_type": "cistern",
    "is_private_wagon": True
}

try:
    result = calculate_freight_tariff(sample_nlu, "расчет перевозки 55т")
    print("=== УСПЕШНЫЙ ЗАПУСК CORE ENGINE 2.0 ===")
    print(f"Режим: {result['shipment_mode']}")
    print(f"Расчетный вес: {result['weight_info']['chargeable_weight']} т")
    print(f"Тарифное расстояние: {result['tariff_dist_km']} км")
    print(f"Итоговый коэффициент: {result['total_coeff']}")
    print(f"Итоговая сумма: {result['total_final_usd']} USD")
except Exception as e:
    print(f"=== ОШИБКА ПРИ ТЕСТЕ: {e} ===")
