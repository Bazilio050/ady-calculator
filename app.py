# 8. Прямой и молниеносный REST-вызов по официальным алиасам API
def call_gemini_direct(prompt, instruction, key):
    # Действующие универсальные алиасы Google API
    candidate_models = [
        "gemini-flash",
        "gemini-pro"
    ]
    
    errors = []
    for model_name in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {
                "parts": [{"text": instruction}]
            },
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }
        
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=20)
            if res.status_code == 200:
                data = res.json()
                text_out = data['candidates'][0]['content']['parts'][0]['text']
                return text_out, model_name
            else:
                errors.append(f"{model_name} (Status {res.status_code}): {res.text}")
        except Exception as e:
            errors.append(f"{model_name}: {str(e)}")

    raise RuntimeError("Ошибка при вызове Google API:\n\n" + "\n\n".join(errors))
