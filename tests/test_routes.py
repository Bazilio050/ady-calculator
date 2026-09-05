from core.router import RailwayRouter


def test_visual_routing():
    router = RailwayRouter(distances_file_path="data/Distances.txt")

    # Входные короткие запросы от пользователя
    test_queries = [
        ("Ялама", "Апшерон"),
        ("Ялама", "Беюк Кясик"),
        ("Беюк Кясик", "Алят"),
        ("Алят экс", "Сальяны"),
        ("Астара", "ТРК"),
        ("Yalama", "Boyuk Kesik"),
        ("Апшерон", "Ялама"),
    ]

    print("\n" + "=" * 70)
    print("      ПРОВЕРКА РЕЗОЛВИНГА, ЕСР-КОДОВ И ТИПА ПЕРЕВОЗКИ ADY")
    print("=" * 70)

    for idx, (raw_from, raw_to) in enumerate(test_queries, 1):
        try:
            res = router.calculate_route(raw_from, raw_to)

            # Формируем итоговую строку вывода
            out = f"{res.from_station.canonical_name} ({res.from_station.code}) - {res.to_station.canonical_name} ({res.to_station.code}) [{res.shipment_type.name}]"

            print(f"\n{idx}. Запрос:         {raw_from} {raw_to}")
            print(f"   Вывод на экран: {out}  ✅")

        except Exception as e:
            print(f"\n{idx}. Запрос:         {raw_from} {raw_to}")
            print(f"   Вывод на экран: Ошибка ({e})  ❌")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    test_visual_routing()
