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
ODDS_API_KEY = "f941db0959abcf753ad321a81aa18a10"

bot = Bot(token=TOKEN)

LEAGUES = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_france_ligue_one",

    "soccer_brazil_campeonato",
    "soccer_brazil_serie_b",

    "soccer_netherlands_eredivisie",
    "soccer_portugal_primeira_liga",
    "soccer_turkey_super_league",

    "soccer_argentina_primera_division",
    "soccer_mexico_ligamx",
    "soccer_usa_mls",

    "soccer_japan_j_league",
    "soccer_korea_kleague1"
]

def prob_por_odd(odd):
    if not odd or odd <= 0:
        return 0
    return (1 / odd) * 100

# ==============================
# PEGAR ODDS OVER 2.5
# ==============================
def extrair_odd(jogo):
    try:
        for book in jogo.get("bookmakers", []):
            for market in book.get("markets", []):
                if market.get("key") == "totals":
                    for o in market.get("outcomes", []):
                        if o.get("name") == "Over" and o.get("point") == 2.5:
                            return o.get("price")
    except:
        return None

# ==============================
# BUSCAR JOGOS (FOCO EM ODDS)
# ==============================
def buscar_jogos():

    agora = datetime.now(UTC)
    limite = agora + timedelta(hours=24)

    entradas = []

    for league in LEAGUES:

        url = f"https://api.the-odds-api.com/v4/sports/{league}/odds"

        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "totals",
            "oddsFormat": "decimal"
        }

        try:
            res = requests.get(url, params=params, timeout=10)
            data = res.json()

            if not isinstance(data, list):
                continue

            for jogo in data:

                home = jogo.get("home_team")
                away = jogo.get("away_team")

                commence = jogo.get("commence_time")
                if not commence:
                    continue

                data_jogo = datetime.fromisoformat(commence.replace("Z", "+00:00"))

                if not (agora <= data_jogo <= limite):
                    continue

                hora = (data_jogo - timedelta(hours=3)).strftime("%H:%M")

                odd = extrair_odd(jogo)

                if not odd:
                    continue

                prob = prob_por_odd(odd)

                print(f"{home} vs {away} | Odd: {odd} | Prob: {prob:.0f}%")

                # ==============================
                # FILTRO MAIS INTELIGENTE
                # ==============================
                if prob < 50:
                    continue

                if prob >= 65:
                    tipo = "🔵 SEGURA"
                elif prob >= 58:
                    tipo = "🟢 BOA"
                else:
                    tipo = "🟡 TESTE"

                entradas.append(f"""{tipo}

{home} x {away}
🕒 {hora}

💰 Odd: {odd}
📊 Probabilidade: {prob:.0f}%
""")

        except Exception as e:
            print("Erro liga:", league, e)

    return entradas[:20]


# ==============================
# TELEGRAM
# ==============================
async def enviar_alerta():

    entradas = buscar_jogos()

    if not entradas:
        print("📊 Nenhuma entrada (API pode estar limitada)")
        return

    msg = "📊 OPORTUNIDADES DO DIA (ODDS REAIS)\n\n"

    for e in entradas:
        msg += e + "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)


# ==============================
# LOOP
# ==============================
async def main():
    print("🚀 Bot rodando (modo ODDS reais)...")

    while True:
        try:
            await enviar_alerta()
        except Exception as e:
            print("Erro geral:", e)

        await asyncio.sleep(600)


# ==============================
# START
# ==============================
if __name__ == "__main__":
    asyncio.run(main())