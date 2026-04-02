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

cache_times = {}

# ==============================
# NORMALIZAR
# ==============================
def normalizar(texto):
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode().lower()

# ==============================
# BUSCAR JOGOS (SEM ODDS)
# ==============================
def buscar_jogos_dia():

    url = "https://api.sofascore.com/api/v1/sport/football/events/live"

    try:
        res = requests.get(url, timeout=10)
        data = res.json()

        jogos = []

        for j in data.get("events", []):
            home = j.get("homeTeam", {}).get("name")
            away = j.get("awayTeam", {}).get("name")
            timestamp = j.get("startTimestamp")

            if not home or not away:
                continue

            data_jogo = datetime.fromtimestamp(timestamp, UTC)
            hora = (data_jogo - timedelta(hours=3)).strftime("%H:%M")

            jogos.append((home, away, hora))

        return jogos

    except Exception as e:
        print("Erro jogos:", e)
        return []

# ==============================
# STATS TIME
# ==============================
def buscar_stats_time(time_nome):

    if time_nome in cache_times:
        return cache_times[time_nome]

    try:
        url_search = f"https://api.sofascore.com/api/v1/search/all?q={time_nome}"
        res = requests.get(url_search, timeout=10)
        data = res.json()

        time_id = None

        for item in data.get("results", []):
            if item.get("entity", {}).get("name"):
                time_id = item["entity"]["id"]
                break

        if not time_id:
            return (0, 0)

        url_games = f"https://api.sofascore.com/api/v1/team/{time_id}/events/last/5"
        res = requests.get(url_games, timeout=10)
        jogos = res.json().get("events", [])

        over15 = 0
        over25 = 0
        validos = 0

        for j in jogos:
            home = j.get("homeScore", {}).get("current")
            away = j.get("awayScore", {}).get("current")

            if not isinstance(home, int) or not isinstance(away, int):
                continue

            total = home + away
            validos += 1

            if total >= 2:
                over15 += 1
            if total >= 3:
                over25 += 1

        if validos == 0:
            return (0, 0)

        prob15 = (over15 / validos) * 100
        prob25 = (over25 / validos) * 100

        cache_times[time_nome] = (prob15, prob25)

        time.sleep(0.5)

        return prob15, prob25

    except Exception as e:
        print("Erro stats:", e)
        return (0, 0)

# ==============================
# ANALISAR JOGOS
# ==============================
def analisar():

    jogos = buscar_jogos_dia()
    entradas = []

    for home, away, hora in jogos:

        try:
            h15, h25 = buscar_stats_time(home)
            a15, a25 = buscar_stats_time(away)

            if h15 == 0 or a15 == 0:
                continue

            prob15 = (h15 + a15) / 2
            prob25 = (h25 + a25) / 2

            print(f"{home} vs {away} | O1.5: {prob15:.0f}% | O2.5: {prob25:.0f}%")

            if prob15 >= 65 or prob25 >= 55:

                if prob25 >= 65:
                    tipo = "🔵 SEGURA"
                elif prob25 >= 58:
                    tipo = "🟢 BOA"
                else:
                    tipo = "🟡 TESTE"

                entradas.append(f"""{tipo}

{home} x {away}
🕒 {hora}

📊 Over 1.5 → {prob15:.0f}%
📊 Over 2.5 → {prob25:.0f}%
""")

        except Exception as e:
            print("Erro jogo:", e)

    return entradas[:20]

# ==============================
# TELEGRAM
# ==============================
async def enviar():

    entradas = analisar()

    if not entradas:
        print("🔁 Sem oportunidades (stats insuficientes)")
        return

    msg = "📊 ENTRADAS DO DIA (MODELO INTELIGENTE)\n\n"

    for e in entradas:
        msg += e + "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)

# ==============================
# LOOP
# ==============================
async def main():
    print("🚀 Bot rodando (sem odds, inteligência própria)...")

    while True:
        await enviar()
        await asyncio.sleep(600)

# ==============================
# START
# ==============================
if __name__ == "__main__":
    asyncio.run(main())