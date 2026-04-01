
import requests
import asyncio
from telegram import Bot
from datetime import datetime, UTC, timedelta
import time

TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "7729625060"
ODDS_API_KEY = "f941db0959abcf753ad321a81aa18a10"
STATS_API_KEY = "SUA_API_KEY_STATS"

bot = Bot(token=TOKEN)

LEAGUES = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_brazil_campeonato",
    "soccer_brazil_serie_b"
]

ultimos_jogos_enviados = set()
cache_times = {}  # 🔥 cache de probabilidade


# ==============================
# 🔥 SOFASCORE STATS
# ==============================
def buscar_stats_sofascore(time_nome):

    # 🔥 CACHE (evita excesso de requisições)
    if time_nome in cache_times:
        return cache_times[time_nome]

    try:
        # 🔍 Buscar ID do time
        url_search = f"https://api.sofascore.com/api/v1/search/all?q={time_nome}"
        res = requests.get(url_search, timeout=10)
        data = res.json()

        time_id = None

        for item in data.get("results", []):
            nome_api = item.get("entity", {}).get("name", "").lower()

            if time_nome.lower() in nome_api:
                time_id = item["entity"]["id"]
                break

        if not time_id:
            cache_times[time_nome] = 0
            return 0

        # 📊 Últimos 5 jogos
        url_games = f"https://api.sofascore.com/api/v1/team/{time_id}/events/last/5"
        res = requests.get(url_games, timeout=10)
        jogos = res.json().get("events", [])

        if not jogos:
            cache_times[time_nome] = 0
            return 0

        over = 0

        for j in jogos:
            home = j["homeScore"]["current"]
            away = j["awayScore"]["current"]

            if home is not None and away is not None:
                if (home + away) >= 2:
                    over += 1

        prob = (over / len(jogos)) * 100

        cache_times[time_nome] = prob

        time.sleep(1)  # 🔥 evitar bloqueio

        return prob

    except Exception as e:
        print("Erro SofaScore:", e)
        cache_times[time_nome] = 0
        return 0


# ==============================
# BUSCAR JOGOS + INTELIGÊNCIA
# ==============================
def buscar_jogos():
    agora = datetime.now(UTC)
    limite = agora + timedelta(hours=12)

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

                    # 🔥 PROBABILIDADE REAL
                    prob_home = buscar_stats_sofascore(home)
                    prob_away = buscar_stats_sofascore(away)

                    prob_final = (prob_home + prob_away) / 2

                    # 🎯 FILTRO
                    if prob_final < 70:
                        continue

                    entradas.append(f"""🧠 ENTRADA INTELIGENTE

{home} x {away}
🕒 {hora}

📊 Probabilidade: {prob_final:.0f}%
🎯 Over 1.5 gols
""")

                    novos_jogos.add(jogo_id)

                except Exception as e:
                    print("Erro jogo:", e)

        except Exception as e:
            print("Erro liga:", league, e)

    return entradas[:10], novos_jogos


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
        print("📊 Nenhuma entrada com probabilidade suficiente")
        return

    msg = "🧠 ENTRADAS COM PROBABILIDADE ALTA\n\n"

    for e in entradas:
        msg += e + "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)


# ==============================
# LOOP
# ==============================
async def main():
    print("🚀 Bot rodando (modo inteligência + SofaScore)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(900)  # 15 min


# ==============================
# START
# ==============================
if __name__ == "__main__":
    asyncio.run(main())