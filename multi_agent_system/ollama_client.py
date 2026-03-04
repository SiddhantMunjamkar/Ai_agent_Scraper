import requests
import json


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL="qwen2.5:7b"


def call_ollama(prompt:str):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
           
            "stream": False,
             "options":{
                "temperature":0
            }
        },
        timeout=320
    )

    if response.status_code !=200:
        raise Exception(f"Ollama error:{response.text}")
    data = response.json()
    print("\n===== OLLAMA RAW RESPONSE =====")
    print(json.dumps(data, indent=2))
    print("================================\n")

    return data["message"]["content"]