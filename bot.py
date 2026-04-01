import requests
import os
import asyncio
from telegram import Bot

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("ODDS_API_KEY")

bot = Bot(token=TOKEN)

BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer/odds"


def buscar_jogos():
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "totals",
        "oddsFormat": "decimal"
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)

        # 🔥 DEBUG REAL
        print("Status Code:", response.status_code)
        print("Resposta:", response.text)

        data = response.json()

        # 🚨 VALIDAÇÃO CRÍTICA
        if not isinstance(data, list):
            return [f"❌ Erro API: {data}"]

        entradas = []

        for jogo in data:
            try:
                home = jogo.get("home_team")
                away = jogo.get("away_team")

                bookmakers = jogo.get("bookmakers", [])

                for book in bookmakers:
                    for market in book.get("markets", []):
                        if market.get("key") == "totals":
                            for outcome in market.get("outcomes", []):
                                if (
                                    outcome.get("name") == "Over"
                                    and outcome.get("point") == 2.5
                                ):
                                    odd = outcome.get("price")

                                    if not odd:
                                        continue

                                    # 🎯 FILTRO
                                    if 1.70 <= odd <= 2.50:

                                        if odd >= 2.0:
                                            nivel = "🟢 EV+"
                                        else:
                                            nivel = "🟡 PADRÃO"

                                        entradas.append(f"""{nivel}

{home} x {away}
🎯 Over 2.5
💰 Odd: {odd}
""")

            except Exception as e:
                print("Erro jogo:", e)
                continue

        if not entradas:
            return ["📊 Nenhuma oportunidade encontrada"]

        return entradas[:10]

    except Exception as e:
        return [f"Erro geral: {str(e)}"]


async def enviar_alerta():
    jogos = buscar_jogos()

    msg = "📊 OPORTUNIDADES DO DIA\n\n"

    for j in jogos:
        msg += j + "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)


async def main():
    print("🚀 Bot rodando (Odds API corrigido)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(600)


if __name__ == "__main__":
    asyncio.run(main())