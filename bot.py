import requests
import asyncio
from telegram import Bot

# ==============================
# CONFIG
# ==============================
TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "7729625060"

# 🔥 API KEY FIXA (resolve 100% problema do Railway)
API_KEY = "f941db0959abcf753ad321a81aa18a10"

bot = Bot(token=TOKEN)

# 🔥 Liga confiável (Premier League)
BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"


# ==============================
# BUSCAR JOGOS + ODDS
# ==============================
def buscar_jogos():
    print("🔍 DEBUG API KEY:", API_KEY)

    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "totals",
        "oddsFormat": "decimal"
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)

        print("📡 STATUS:", response.status_code)
        print("📡 RESPOSTA:", response.text)

        data = response.json()

        # 🚨 VALIDAÇÃO
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

                                    # 🎯 FILTRO AJUSTADO
                                    if 1.50 <= odd <= 2.80:

                                        if odd >= 2.10:
                                            nivel = "🟢 EV+ FORTE"
                                        elif odd >= 1.80:
                                            nivel = "🟡 BOA"
                                        else:
                                            nivel = "🔵 SEGURA"

                                        entradas.append(f"""{nivel}

{home} x {away}
🎯 Over 2.5 gols
💰 Odd: {odd}
""")

            except Exception as e:
                print("Erro jogo:", e)
                continue

        if not entradas:
            return ["📊 Sem oportunidades no momento"]

        return entradas[:10]

    except Exception as e:
        return [f"Erro geral: {str(e)}"]


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
    print("🚀 Bot rodando (modo funcional)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(600)  # 10 minutos


# ==============================
# START
# ==============================
if __name__ == "__main__":
    asyncio.run(main())