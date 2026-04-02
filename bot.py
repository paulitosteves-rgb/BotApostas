import requests

print("Testando internet...")

try:
    r = requests.get("https://www.google.com", timeout=5)
    print("Status:", r.status_code)
except Exception as e:
    print("Erro:", e)