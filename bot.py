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


def fazer_request(url):
    headers = {"x-apisports-key": API_KEY}
    try:
        return requests.get(url, headers=headers, timeout=10).json()
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

    resultados = []

    for league in LEAGUES:
        url = f"{BASE_URL}/fixtures?date={hoje}&league={league}"
        data = fazer_request(url)

        if not data or not data["response"]:
            continue

        for jogo in data["response"]:
            try:
                home = jogo["teams"]["home"]["name"]
                away = jogo["teams"]["away"]["name"]

                home_id = jogo["teams"]["home"]["id"]
                away_id = jogo["teams"]["away"]["id"]

                stats_home = get_team_stats(home_id)
                stats_away = get_team_stats(away_id)

                # 🔥 CASO 1: TEM DADOS
                if stats_home and stats_away:
                    media_total = (stats_home + stats_away) / 2

                    resultados.append(f"""🔥 OPORTUNIDADE

{home} x {away}
Over 2.5 gols
📊 Média: {round(media_total,2)}
""")

                # 🔥 CASO 2: SEM DADOS (NÃO DESCARTA MAIS)
                else:
                    resultados.append(f"""📊 JOGO DO DIA

{home} x {away}
⚠️ Sem estatística suficiente
""")

            except Exception as e:
                print("Erro jogo:", e)

    # 🔥 GARANTIA FINAL
    if not resultados:
        return ["🚨 ERRO: API não retornou jogos"]

    return resultados[:10]


async def enviar_alerta():
    jogos = buscar_jogos()

    msg = "📊 ENTRADAS DO DIA\n\n"

    for j in jogos:
        msg += j + "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)


async def main():
    print("🚀 Bot rodando (modo estável real)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(main())