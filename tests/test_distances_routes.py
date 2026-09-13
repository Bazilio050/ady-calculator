import pytest
from core.router import RailwayRouter

def test_check_eight_routes_km():
    """Сверка 8 ключевых маршрутов ADY на точный километраж"""
    router = RailwayRouter(distances_file_path="data/distances.csv")
    
    routes_to_check = [
        ("Ялама", "Апшерон"),
        ("Хырдалан", "Ялама"),
        ("Алят-эксп.", "Беюк Кясик"),
        ("Сальяны", "Курык"),
        ("Беюк Кясик", "ТРК"),
        ("Карадаг", "Астара"),
        ("Ялама", "Астара"),
        ("Астара", "Баладжары"),
        ("Ялама", "Хачмаз"),
        ("Ленкорань", "Астара"),
    ]
    
    print("\n" + "="*50)
    print(f"{'МАРШРУТ':<30} | {'РАСЧЕТНЫЙ КМ':<15}")
    print("="*50)
    
    for from_st, to_st in routes_to_check:
        res = router.calculate_route(from_st, to_st)
        print(f"{from_st + ' — ' + to_st:<30} | {res.calculated_distance_km:<15}")
    
    print("="*50 + "\n")
