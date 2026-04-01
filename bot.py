import requests
import os
import asyncio
from datetime import datetime
from telegram import Bot

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_KEY")

bot = Bot(token=TOKEN)

BASE_URL = "https://v3.football.api-sports.io"


def buscar_jogos():
    hoje = datetime.now().strftime("%Y-%m-%d")

    url = f"{BASE_URL}/fixtures?date={hoje}"

    headers = {"x-apisports-key": API_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if not data or not data["response"]:
            return ["⚠️ API sem jogos no momento"]

        jogos = []

        for jogo in data["response"][:10]:
            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            league = jogo["league"]["name"]

            jogos.append(f"""⚽ {home} x {away}
🏆 {league}
""")

        return jogos

    except Exception as e:
        return [f"Erro API: {str(e)}"]


async def enviar_alerta():
    jogos = buscar_jogos()

    msg = "📊 JOGOS DO DIA\n\n"

    for j in jogos:
        msg += j + "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)


async def main():
    print("🚀 Bot rodando (modo leve - sem limite)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(main())