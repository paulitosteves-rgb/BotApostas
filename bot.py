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
team_cache = {}

LEAGUES = [39, 140, 135, 78, 61, 71]
STATUS_VALIDOS = ["NS", "LIVE"]


def fazer_request(url):
    headers = {"x-apisports-key": API_KEY}
    try:
        return requests.get(url, headers=headers, timeout=10).json()
    except:
        return None


def get_odds(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    data = fazer_request(url)

    try:
        for book in data["response"][0]["bookmakers"]:
            for bet in book["bets"]:
                if bet["name"] == "Goals Over/Under":
                    for v in bet["values"]:
                        if v["value"] == "Over 2.5":
                            return float(v["odd"])
    except:
        return None


def get_team_stats(team_id):
    if team_id in team_cache:
        return team_cache[team_id]

    url = f"{BASE_URL}/fixtures?team={team_id}&last=5"
    data = fazer_request(url)

    if not data or not data["response"]:
        return None

    gols = 0
    jogos = 0

    for j in data["response"]:
        if j["goals"]["home"] is None:
            continue

        gols += j["goals"]["home"] + j["goals"]["away"]
        jogos += 1

    if jogos == 0:
        return None

    media = gols / jogos
    team_cache[team_id] = media
    return media


def buscar_jogos():
    hoje = datetime.now().strftime("%Y-%m-%d")

    entradas = []

    for league in LEAGUES:
        url = f"{BASE_URL}/fixtures?date={hoje}&league={league}"
        data = fazer_request(url)

        if not data:
            continue

        for jogo in data["response"]:
            if jogo["fixture"]["status"]["short"] not in STATUS_VALIDOS:
                continue

            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            fixture_id = jogo["fixture"]["id"]

            media_home = get_team_stats(jogo["teams"]["home"]["id"])
            media_away = get_team_stats(jogo["teams"]["away"]["id"])

            if not media_home or not media_away:
                continue

            media_total = (media_home + media_away) / 2
            prob = media_total / 4

            odd = get_odds(fixture_id)

            # 🟢 COM ODDS (EV)
            if odd:
                prob_odd = 1 / odd

                if prob > prob_odd:
                    entradas.append(f"""🟢 EV+

{home} x {away}
Over 2.5
Odd: {odd}
Prob: {round(prob*100)}%
""")
                else:
                    entradas.append(f"""🟡 QUASE

{home} x {away}
Over 2.5
Odd: {odd}
Prob: {round(prob*100)}%
""")

            # 🔵 SEM ODDS (não descarta mais)
            else:
                if prob > 0.60:
                    entradas.append(f"""🔵 PROBABILIDADE ALTA

{home} x {away}
Over 2.5
Prob: {round(prob*100)}%
""")

    if not entradas:
        return ["⚠️ Nenhuma entrada — revisar API ou stats"]

    return entradas[:10]


async def enviar_alerta():
    jogos = buscar_jogos()

    msg = "📊 ENTRADAS DO DIA\n\n"

    for j in jogos:
        msg += j + "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)


async def main():
    print("🚀 Bot rodando (modo produção real)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(main())