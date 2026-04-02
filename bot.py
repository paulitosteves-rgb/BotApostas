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
    print("🔍 Buscando jogos...")

    try:
        url = "https://www.scorebat.com/video-api/v3/"
        res = requests.get(url, timeout=5)

        data = res.json()

        jogos = []

        for item in data.get("response", []):
            titulo = item.get("title", "")

            if " vs " in titulo:
                home, away = titulo.split(" vs ")
                jogos.append((home.strip(), away.strip()))

        if jogos:
            print(f"✅ {len(jogos)} jogos encontrados")
            return jogos[:10]

    except Exception as e:
        print("⚠️ erro externo:", e)

    print("⚠️ fallback ativado")

    return [
        ("Time A", "Time B"),
        ("Time C", "Time D"),
        ("Time E", "Time F"),
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