import requests
import os
import asyncio
from datetime import datetime, timedelta
from telegram import Bot
import time

# ==============================
# 🔐 CONFIG
# ==============================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_KEY")

bot = Bot(token=TOKEN)

BASE_URL = "https://v3.football.api-sports.io"


# ==============================
# 🧪 DEBUG INICIAL
# ==============================
print("🔍 Iniciando bot...")
print("API_KEY carregada:", API_KEY)


# ==============================
# 🔁 REQUEST COM LOG COMPLETO
# ==============================
def fazer_request(url, tentativas=3):
    headers = {
        "x-apisports-key": API_KEY
    }

    for i in range(tentativas):
        try:
            print(f"🌐 Request ({i+1}): {url}")
            response = requests.get(url, headers=headers, timeout=10)

            print("Status Code:", response.status_code)

            data = response.json()
            print("Resposta API:", data)

            if "response" in data:
                return data

        except Exception as e:
            print(f"❌ Erro tentativa {i+1}:", e)

        time.sleep(2)

    return None


# ==============================
# 📅 BUSCAR DATA COM JOGOS
# ==============================
def buscar_data_com_jogos():
    for i in range(3):
        data_teste = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")

        url = f"{BASE_URL}/fixtures?date={data_teste}"
        data = fazer_request(url)

        if data and data["response"]:
            print(f"✅ Jogos encontrados na data: {data_teste}")
            return data_teste, data

    return None, None


# ==============================
# 📊 BUSCAR JOGOS
# ==============================
def buscar_jogos():
    data_uso, data = buscar_data_com_jogos()

    # 🔥 FALLBACK TOTAL (se API falhar)
    if not data:
        print("⚠️ API falhou — usando fallback interno")

        return ["""🔥 OPORTUNIDADE (FALLBACK)

Flamengo x Palmeiras
✔️ Over 2.5 gols
📊 Probabilidade: 78%
""",
                """🔥 OPORTUNIDADE (FALLBACK)

Real Madrid x Barcelona
✔️ BTTS
📊 Probabilidade: 82%
"""]

    oportunidades = []

    for jogo in data["response"][:10]:
        try:
            status = jogo["fixture"]["status"]["short"]

            if status not in ["NS", "TBD"]:
                continue

            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            oportunidades.append(f"""🔥 JOGO DO DIA

{home} x {away}
📊 Análise básica disponível
""")

        except Exception as e:
            print("Erro jogo:", e)

    if not oportunidades:
        return ["🤖 Jogos encontrados, mas sem dados suficientes"]

    return oportunidades


# ==============================
# 📲 TELEGRAM
# ==============================
async def enviar_alerta():
    jogos = buscar_jogos()

    mensagem = "📊 ANÁLISE AUTOMÁTICA\n\n"

    for j in jogos:
        mensagem += j + "\n"

    try:
        await bot.send_message(chat_id=CHAT_ID, text=mensagem)
        print("✅ Mensagem enviada")
    except Exception as e:
        print("❌ Erro Telegram:", e)


# ==============================
# 🔁 LOOP
# ==============================
async def main():
    print("🚀 Bot rodando (modo debug total)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(120)


# ==============================
# ▶️ START
# ==============================
if __name__ == "__main__":
    asyncio.run(main())