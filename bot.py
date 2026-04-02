import requests
import asyncio
from telegram import Bot
from datetime import datetime, UTC, timedelta
import time
import unicodedata

# ==============================
# CONFIG
# ==============================
TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "7729625060"
RAPID_KEY = "44f6eed408msh75ed9220e2e8145p12354djsne37a59298723"

# ==============================
# TELEGRAM
# ==============================
def enviar(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

# ==============================
# BUSCAR JOGOS DO DIA (API-FOOTBALL)
# ==============================
def buscar_jogos():

    hoje = datetime.now().strftime("%Y-%m-%d")

    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"

    headers = {
        "X-RapidAPI-Key": RAPID_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    params = {"date": hoje}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        data = res.json()

        jogos = []

        for j in data.get("response", []):

            home = j["teams"]["home"]["name"]
            away = j["teams"]["away"]["name"]

            timestamp = j["fixture"]["timestamp"]
            hora = datetime.fromtimestamp(timestamp).strftime("%H:%M")

            jogos.append((home, away, hora))

        print(f"📊 Jogos encontrados: {len(jogos)}")

        return jogos

    except Exception as e:
        print("Erro jogos:", e)
        return []

# ==============================
# LÓGICA SIMPLES (TEMPORÁRIA)
# ==============================
def analisar():

    jogos = buscar_jogos()
    entradas = []

    for home, away, hora in jogos:

        # 🔥 modelo simples para garantir volume
        entradas.append(f"""🟡 JOGO

{home} x {away}
🕒 {hora}

📊 Monitoramento ativo
""")

    return entradas[:20]

# ==============================
# LOOP
# ==============================
async def main():
    print("🚀 Bot rodando (API-Football)...")

    while True:

        entradas = analisar()

        if entradas:
            msg = "📊 JOGOS DO DIA\n\n"
            for e in entradas:
                msg += e + "\n"

            enviar(msg)
        else:
            print("🔁 Sem jogos")

        await asyncio.sleep(600)

# ==============================
# START
# ==============================
if __name__ == "_main_":
    asyncio.run(main())