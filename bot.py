import requests
import asyncio
from datetime import datetime
import time

# ==============================
# CONFIG
# ==============================
TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "7729625060"

def enviar(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except Exception as e:
        print("Erro Telegram:", e)

def buscar_jogos():
    print("🔍 Buscando jogos ESPN...")

    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"
        res = requests.get(url, timeout=5)

        data = res.json()
        jogos = []

        for event in data.get("events", []):

            comp = event.get("competitions", [])[0]
            teams = comp.get("competitors", [])

            if len(teams) < 2:
                continue

            home = teams[0]["team"]["name"]
            away = teams[1]["team"]["name"]

            hora = event.get("date", "")[11:16]

            jogos.append((home, away, hora))

        if jogos:
            print(f"✅ {len(jogos)} jogos reais encontrados")
            return jogos[:15]

    except Exception as e:
        print("⚠️ erro ESPN:", e)

    print("⚠️ fallback ativado")

    return [
        ("Time A", "Time B"),
        ("Time C", "Time D"),
    ]

# ==============================
# LOOP PRINCIPAL (SIMPLES)
# ==============================
print("🚀 BOT INICIADO (MODO ESTÁVEL)")

while True:
    try:
        jogos = buscar_jogos()

        msg = "📊 JOGOS DO DIA\n\n"

        for home, away in jogos:
            msg += f"{home} x {away}\n"

        print("📤 Enviando mensagem...")
        enviar(msg)

    except Exception as e:
        print("💥 ERRO LOOP:", e)

    time.sleep(30)  # 30s pra debug