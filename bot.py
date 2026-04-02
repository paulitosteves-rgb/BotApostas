import requests
import asyncio
from datetime import datetime
import time

# ==============================
# CONFIG
# ==============================
TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "7729625060"

# ==============================
# TELEGRAM
# ==============================
def enviar(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=3)
    except Exception as e:
        print("Erro Telegram:", e)

# ==============================
# BUSCAR JOGOS (ULTRA SEGURO)
# ==============================
def buscar_jogos():

    print("🔍 Buscando jogos...")

    try:
        url = "https://www.scorebat.com/video-api/v3/"

        res = requests.get(url, timeout=3)

        if res.status_code != 200:
            raise Exception("Status inválido")

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
        print("⚠️ Falha externa:", e)

    # 🔥 fallback garantido
    print("⚠️ usando fallback local")

    return [
        ("Time A", "Time B"),
        ("Time C", "Time D"),
        ("Time E", "Time F"),
    ]

# ==============================
# LOOP
# ==============================
async def main():

    print("🚀 BOT INICIADO COM SUCESSO")

    while True:

        try:
            jogos = buscar_jogos()

            msg = "📊 JOGOS DO DIA\n\n"

            for home, away in jogos:
                msg += f"{home} x {away}\n"

            print("📤 Enviando...")
            enviar(msg)

        except Exception as e:
            print("💥 ERRO LOOP:", e)

        await asyncio.sleep(10)  # curto pra debug

# ==============================
# START
# ==============================
if __name__ == "_main_":
    asyncio.run(main())