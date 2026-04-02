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

ultimos_jogos_enviados = set()
cache_times = {}

# ==============================
# NORMALIZAR TEXTO
# ==============================
def normalizar(texto):
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode().lower()

# ==============================
# ODD -> PROB
# ==============================
def prob_por_odd(odd):
    if not odd or odd <= 0:
        return 0
    return (1 / odd) * 100

# ==============================
# PEGAR ODD OVER 2.5
# ==============================
def extrair_odd_over25(jogo):
    try:
        for book in jogo.get("bookmakers", []):
            for market in book.get("markets", []):
                if market.get("key") == "totals":
                    for outcome in market.get("outcomes", []):
                        if outcome.get("name") == "Over" and outcome.get("point") == 2.5:
                            return outcome.get("price")
    except:
        return None

# ==============================
# SOFASCORE STATS
# ==============================
def buscar_stats_sofascore(time_nome):

    if time_nome in cache_times:
        return cache_times[time_nome]

    try:
        nome_input = normalizar(time_nome)

        url_search = f"https://api.sofascore.com/api/v1/search/all?q={time_nome}"
        res = requests.get(url_search, timeout=10)
        data = res.json()

        time_id = None

        for item in data.get("results", []):
            nome_api = normalizar(item.get("entity", {}).get("name", ""))

            if nome_input in nome_api or nome_api in nome_input:
                time_id = item["entity"]["id"]
                break

        if not time_id:
            cache_times[time_nome] = (0, 0)
            return 0, 0

        url_games = f"https://api.sofascore.com/api/v1/team/{time_id}/events/last/5"
        res = requests.get(url_games, timeout=10)
        jogos = res.json().get("events", [])

        if not jogos:
            cache_times[time_nome] = (0, 0)
            return 0, 0

        over15 = 0
        over25 = 0
        validos = 0

        for j in jogos:

            home = j.get("homeScore", {}).get("current")
            away = j.get("awayScore", {}).get("current")

            if home is None:
                home = j.get("homeScore", {}).get("display")

            if away is None:
                away = j.get("awayScore", {}).get("display")

            if home is None or away is None:
                continue

            if not isinstance(home, int) or not isinstance(away, int):
                continue

            total = home + away
            validos += 1

            if total >= 2:
                over15 += 1
            if total >= 3:
                over25 += 1

        if validos == 0:
            cache_times[time_nome] = (0, 0)
            return 0, 0

        prob15 = (over15 / validos) * 100
        prob25 = (over25 / validos) * 100

        cache_times[time_nome] = (prob15, prob25)

        time.sleep(0.5)

        return prob15, prob25

    except Exception as e:
        print("Erro SofaScore:", e)
        cache_times[time_nome] = (0, 0)
        return 0, 0


# ==============================
# BUSCAR JOGOS
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
                try:
                    home = jogo.get("home_team")
                    away = jogo.get("away_team")

                    jogo_id = f"{home} x {away}"

                    if jogo_id in novos_jogos:
                        continue

                    commence_time = jogo.get("commence_time")
                    if not commence_time:
                        continue

                    data_jogo = datetime.fromisoformat(
                        commence_time.replace("Z", "+00:00")
                    )

                    if not (agora <= data_jogo <= limite):
                        continue

                    hora = (data_jogo - timedelta(hours=3)).strftime("%H:%M")

                    # ==============================
                    # STATS
                    # ==============================
                    prob_home_15, prob_home_25 = buscar_stats_sofascore(home)
                    prob_away_15, prob_away_25 = buscar_stats_sofascore(away)

                    # ==============================
                    # OVER 1.5 (MAIS FLEXÍVEL)
                    # ==============================
                    if prob_home_15 == 0 or prob_away_15 == 0:
                        prob15 = 55
                    else:
                        prob15 = (prob_home_15 + prob_away_15) / 2

                    # ==============================
                    # OVER 2.5 (HÍBRIDO)
                    # ==============================
                    odd_over25 = extrair_odd_over25(jogo)

                    if prob_home_25 > 0 and prob_away_25 > 0:
                        prob25 = (prob_home_25 + prob_away_25) / 2
                        origem = "📊 REAL"

                    elif odd_over25:
                        prob25 = prob_por_odd(odd_over25)
                        origem = "💰 ODDS"

                    else:
                        prob25 = 55
                        origem = "⚠️ ESTIMADO"

                    print(f"{home} vs {away} | FINAL: {prob25:.0f}% | {origem}")

                    # ==============================
                    # CLASSIFICAÇÃO NOVA
                    # ==============================
                    if prob25 >= 65:
                        tipo = "🔵 SEGURA"
                    elif prob25 >= 58:
                        tipo = "🟢 BOA"
                    else:
                        tipo = "🟡 TESTE"

                    # ==============================
                    # FILTROS MAIS LEVES
                    # ==============================
                    if prob15 >= 50:
                        entradas.append(f"""{tipo}

{home} x {away}
🕒 {hora}

📊 Over 1.5 → {prob15:.0f}%
""")

                    if prob25 >= 52:
                        entradas.append(f"""{tipo}

{home} x {away}
🕒 {hora}

{origem}
📊 Over 2.5 → {prob25:.0f}%
💰 Odd → {odd_over25 if odd_over25 else "N/A"}
""")

                    novos_jogos.add(jogo_id)

                except Exception as e:
                    print("Erro jogo:", e)

        except Exception as e:
            print("Erro liga:", league, e)

    return entradas[:30], novos_jogos


# ==============================
# TELEGRAM
# ==============================
async def enviar_alerta():
    global ultimos_jogos_enviados

    entradas, novos_jogos = buscar_jogos()

    if novos_jogos == ultimos_jogos_enviados:
        print("🔁 Sem novidades")
        return

    ultimos_jogos_enviados = novos_jogos

    if not entradas:
        print("📊 Nenhuma entrada encontrada")
        return

    msg = "📊 ENTRADAS DO DIA (VOLUME)\n\n"

    for e in entradas:
        msg += e + "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)


# ==============================
# LOOP
# ==============================
async def main():
    print("🚀 Bot rodando (modo volume)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(600)


# ==============================
# START
# ==============================
if __name__ == "__main__":
    asyncio.run(main())