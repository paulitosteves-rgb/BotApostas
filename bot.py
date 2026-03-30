import requests
import os
import asyncio
from datetime import datetime
from telegram import Bot
import time

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_KEY")

bot = Bot(token=TOKEN)

BASE_URL = "https://v3.football.api-sports.io"
team_cache = {}

LEAGUES = [39, 140, 135, 78, 61, 71]
STATUS_VALIDOS = ["NS"]


def fazer_request(url):
    headers = {"x-apisports-key": API_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.json()
    except:
        return None


def get_odds(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    data = fazer_request(url)

    try:
        bookmakers = data["response"][0]["bookmakers"]

        for book in bookmakers:
            for bet in book["bets"]:
                if bet["name"] == "Goals Over/Under":
                    for value in bet["values"]:
                        if value["value"] == "Over 2.5":
                            return float(value["odd"])
    except:
        return None

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
    oportunidades = []

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

            home_id = jogo["teams"]["home"]["id"]
            away_id = jogo["teams"]["away"]["id"]

            fixture_id = jogo["fixture"]["id"]

            media_home = get_team_stats(home_id)
            media_away = get_team_stats(away_id)

            if not media_home or not media_away:
                continue

            media_total = (media_home + media_away) / 2
            prob = media_total / 4  # escala simples

            odd = get_odds(fixture_id)

            if not odd:
                continue

            prob_odd = 1 / odd

            # 🔥 FILTRO EV+
            if prob > prob_odd:
                oportunidades.append(f"""🔥 ENTRADA DE VALOR

{home} x {away}
🎯 Over 2.5 gols

📊 Prob: {round(prob*100)}%
💰 Odd: {odd}
📈 Valor: POSITIVO
""")

    if not oportunidades:
        return ["📊 Sem entradas de valor agora"]

    return oportunidades[:5]


async def enviar_alerta():
    jogos = buscar_jogos()

    msg = "💰 OPORTUNIDADES EV+\n\n"

    for j in jogos:
        msg += j + "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)


async def main():
    print("🚀 Bot EV+ rodando...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(main())