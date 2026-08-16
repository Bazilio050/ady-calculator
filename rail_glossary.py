import os

def get_rail_vocabulary():
    """
    Автоматически собирает актуальный словарь ж/д терминов для STT (Gemini).
    """
    # 1. Фиксированный ж/д сленг (всегда актуален)
    vocabulary = [
        "ГНГ", "GNG", "NHM", "ЕСР", "СПС", "MPS", "SPS", "МПС", "АРВ", 
        "ADY", "БМТ", "UN", "фрахт", "теплушка", "крытый", "полувагон", 
        "платформа", "контейнер", "цистерна", "транспортер", "негабарит"
    ]

    # 2. Динамическое чтение станций из Distances.txt
    if os.path.exists("Distances.txt"):
        try:
            with open("Distances.txt", "r", encoding="utf-8") as f:
                for line in f:
                    # Предполагаем, что название станции — это первое слово или часть строки
                    # Просто добавляем всё, что есть в Distances, чтобы модель знала все пункты
                    parts = line.split(',')
                    if parts:
                        vocabulary.append(parts[0].strip())
        except:
            pass

    # 3. Динамическое чтение грузов из Security_Cargo_GNG.txt
    if os.path.exists("Security_Cargo_GNG.txt"):
        try:
            with open("Security_Cargo_GNG.txt", "r", encoding="utf-8") as f:
                for line in f:
                    # Добавляем названия грузов для распознавания
                    parts = line.split('|')
                    if len(parts) > 1:
                        vocabulary.append(parts[1].strip())
        except:
            pass

    return ", ".join(list(set(vocabulary)))

# Этот блок можно вызвать для теста
if __name__ == "__main__":
    print(get_rail_vocabulary())
