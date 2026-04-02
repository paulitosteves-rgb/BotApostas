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
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except:
        print("Erro Telegram")

# ==============================
# SCRAPING SIMPLES
# ==============================
def buscar_jogos():

    try:
        url = "https://www.scorebat.com/video-api/v3/"
        res = requests.get(url, timeout=5)

        data = res.json()

        jogos = []

        for item in data.get("response", []):

            titulo = item.get("title", "")

            if "vs" in titulo:
                partes = titulo.split(" vs ")

                if len(partes) == 2:
                    home = partes[0].strip()
                    away = partes[1].strip()

                    jogos.append((home, away, "HOJE"))

        print(f"📊 Jogos encontrados: {len(jogos)}")

        if jogos:
            return jogos[:20]

    except Exception as e:
        print("Erro scraping:", e)

    return []

# ==============================
# LÓGICA SIMPLES (BASE INICIAL)
# ==============================
def analisar():

    jogos = buscar_jogos()

    entradas = []

    for home, away, hora in jogos:

        entradas.append(f"""🟡 JOGO

{home} x {away}
🕒 {hora}

📊 Acompanhamento ativo
""")

    return entradas

# ==============================
# LOOP
# ==============================
async def main():
    print("🚀 Bot rodando (modo scraping)...")

    while True:

        entradas = analisar()

        if entradas:
            msg = "📊 JOGOS DO DIA (SCRAPING)\n\n"
            for e in entradas:
                msg += e + "\n"

            enviar(msg)
        else:
            print("🔁 Sem jogos encontrados")

        await asyncio.sleep(600)

# ==============================
# START
# ==============================
if __name__ == "_main_":
    asyncio.run(main())