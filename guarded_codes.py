import os

def load_guarded_codes():
    guarded_set = set()
    file_path = "Security_Cargo_GNG.txt"
    
    if not os.path.exists(file_path):
        return guarded_set
        
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("|") and "**" in line:
                parts = line.split("|")
                if len(parts) > 1:
                    code_raw = parts[1].replace("*", "").strip()
                    if code_raw.isdigit():
                        guarded_set.add(code_raw.zfill(8))
                        
    return guarded_set

GUARDED_8DIGIT_SET = load_guarded_codes()

def is_cargo_guarded(gng_code: str) -> bool:
    """
    Проверяет, входит ли код ГНГ в список охраняемых грузов.
    """
    if not gng_code:
        return False
        
    clean_input = str(gng_code).strip().lstrip('0')
    if not clean_input or not clean_input.isdigit():
        return False

    for guarded_code in GUARDED_8DIGIT_SET:
        guarded_clean = guarded_code.lstrip('0')
        if guarded_clean.startswith(clean_input) or clean_input.startswith(guarded_clean[:len(clean_input)]):
            return True
            
    return False
