import requests
import os
import asyncio
from telegram import Bot

# ==============================
# CONFIG
# ==============================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("ODDS_API_KEY")

bot = Bot(token=TOKEN)

BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer/odds"


# ==============================
# BUSCAR JOGOS + ODDS
# ==============================
def buscar_jogos():
    url = BASE_URL

    params = {
        "apiKey": API_KEY,
        "regions": "eu",  # odds europeias (melhores)
        "markets": "totals",
        "oddsFormat": "decimal"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if not data:
            return ["⚠️ Nenhum dado retornado"]

        entradas = []

        for jogo in data:
            try:
                home = jogo["home_team"]
                away = jogo["away_team"]

                bookmakers = jogo.get("bookmakers", [])

                for book in bookmakers:
                    for market in book["markets"]:
                        if market["key"] == "totals":
                            for outcome in market["outcomes"]:
                                if outcome["name"] == "Over" and outcome["point"] == 2.5:

                                    odd = outcome["price"]

                                    # 🎯 FILTRO PRINCIPAL
                                    if 1.70 <= odd <= 2.50:

                                        # 🔥 CLASSIFICAÇÃO
                                        if odd >= 2.0:
                                            nivel = "🟢 EV+ (ODD ALTA)"
                                        else:
                                            nivel = "🟡 PADRÃO"

                                        entradas.append(f"""{nivel}

{home} x {away}
🎯 Over 2.5 gols
💰 Odd: {odd}
""")

            except Exception as e:
                print("Erro jogo:", e)
                continue

        if not entradas:
            return ["📊 Sem oportunidades dentro do filtro"]

        return entradas[:10]

    except Exception as e:
        return [f"Erro API: {str(e)}"]


# ==============================
# TELEGRAM
# ==============================
async def enviar_alerta():
    jogos = buscar_jogos()

    msg = "📊 OPORTUNIDADES DO DIA\n\n"

    for j in jogos:
        msg += j + "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)


# ==============================
# LOOP
# ==============================
async def main():
    print("🚀 Bot rodando (The Odds API)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(600)  # 10 min (economiza requests)


# ==============================
# START
# ==============================
if __name__ == "__main__":
    asyncio.run(main())