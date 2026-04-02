import requests
import asyncio
from datetime import datetime, UTC, timedelta
import time
import unicodedata
import os

# ==============================
# CONFIG (ENV)
# ==============================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

if not TOKEN or not CHAT_ID or not ODDS_API_KEY:
    raise Exception("❌ Variáveis de ambiente não configuradas!")

# ==============================
# TELEGRAM VIA HTTP
# ==============================
def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Erro Telegram:", e)

# ==============================
# CONFIG
# ==============================
LEAGUES = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_brazil_campeonato",
    "soccer_argentina_primera_division",
]

ultimos_jogos_enviados = set()
cache_times = {}

# ==============================
# NORMALIZAR
# ==============================
def normalizar(texto):
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode().lower()

# ==============================
# PROB POR ODD
# ==============================
def prob_por_odd(odd):
    if not odd or odd <= 0:
        return 0
    return (1 / odd) * 100

# ==============================
# PEGAR ODDS
# ==============================
def extrair_odds(jogo):
    try:
        for book in jogo.get("bookmakers", []):
            for market in book.get("markets", []):
                if market.get("key") == "totals":
                    for outcome in market.get("outcomes", []):
                        if outcome.get("name") == "Over" and outcome.get("point") == 2.5:
                            return outcome.get("price")
        return None
    except:
        return None

# ==============================
# BUSCAR JOGOS (SIMPLIFICADO)
# ==============================
def buscar_jogos():

    agora = datetime.now(UTC)
    limite = agora + timedelta(hours=24)

    entradas = []
    novos_jogos = set()

    for league in LEAGUES:

        url = f"https://api.the-odds-api.com/v4/sports/{league}/odds"

        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "totals",
            "oddsFormat": "decimal"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if not isinstance(data, list):
                continue

            for jogo in data:

                home = jogo.get("home_team")
                away = jogo.get("away_team")

                jogo_id = f"{home} x {away}"
                if jogo_id in novos_jogos:
                    continue

                commence_time = jogo.get("commence_time")
                if not commence_time:
                    continue

                data_jogo = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))

                if not (agora <= data_jogo <= limite):
                    continue

                hora = (data_jogo - timedelta(hours=3)).strftime("%H:%M")

                odd = extrair_odds(jogo)
                prob = prob_por_odd(odd)

                print(f"{home} vs {away} | Odd: {odd} | Prob: {prob:.0f}%")

                if prob < 55:
                    continue

                entradas.append(f"""
{home} x {away}
🕒 {hora}

💰 Odd: {odd}
📊 Prob: {prob:.0f}%
""")

                novos_jogos.add(jogo_id)

        except Exception as e:
            print("Erro liga:", league, e)

    return entradas[:20], novos_jogos


# ==============================
# LOOP
# ==============================
async def main():
    print("🚀 Bot rodando (deploy OK)...")

    while True:
        try:
            entradas, novos = buscar_jogos()

            if entradas:
                msg = "📊 OPORTUNIDADES\n\n"
                for e in entradas:
                    msg += e + "\n"

                enviar_telegram(msg)
            else:
                print("🔁 Sem entradas")

        except Exception as e:
            print("Erro geral:", e)

        await asyncio.sleep(600)


# ==============================
# START
# ==============================
if __name__ == "__main__":
    asyncio.run(main())