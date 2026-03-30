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

team_cache = {}

BASE_URL = "https://v3.football.api-sports.io"

# 🔥 LIGAS PRIORITÁRIAS
LEAGUES = [39, 140, 78, 135, 71, 94]  
# Inglaterra, Espanha, Alemanha, Itália, França, Brasil


def fazer_request(url, tentativas=3):
    headers = {"x-apisports-key": API_KEY}

    for i in range(tentativas):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()

            if "response" in data:
                return data

        except Exception as e:
            print("Erro:", e)

        time.sleep(2)

    return None


def get_team_stats(team_id):
    if team_id in team_cache:
        return team_cache[team_id]

    url = f"{BASE_URL}/fixtures?team={team_id}&last=5"
    data = fazer_request(url)

    if not data:
        return None

    gols_feitos = 0
    gols_sofridos = 0
    jogos = 0

    for jogo in data["response"]:
        g_home = jogo["goals"]["home"]
        g_away = jogo["goals"]["away"]

        if g_home is None or g_away is None:
            continue

        if jogo["teams"]["home"]["id"] == team_id:
            gols_feitos += g_home
            gols_sofridos += g_away
        else:
            gols_feitos += g_away
            gols_sofridos += g_home

        jogos += 1

    if jogos == 0:
        return None

    stats = {
        "media_feitos": gols_feitos / jogos,
        "media_sofridos": gols_sofridos / jogos
    }

    team_cache[team_id] = stats
    return stats


def buscar_jogos():
    data_hoje = datetime.now().strftime("%Y-%m-%d")

    oportunidades = []

    for league in LEAGUES:
        url = f"{BASE_URL}/fixtures?date={data_hoje}&league={league}"
        data = fazer_request(url)

        if not data:
            continue

        for jogo in data["response"]:
            try:
                status = jogo["fixture"]["status"]["short"]

                if status not in ["NS", "TBD"]:
                    continue

                home = jogo["teams"]["home"]["name"]
                away = jogo["teams"]["away"]["name"]

                home_id = jogo["teams"]["home"]["id"]
                away_id = jogo["teams"]["away"]["id"]

                stats_home = get_team_stats(home_id)
                stats_away = get_team_stats(away_id)

                # 🔥 SE NÃO TEM STATS → AINDA MANDA
                if not stats_home or not stats_away:
                    oportunidades.append(f"""🔥 JOGO DO DIA

{home} x {away}
📊 Sem dados suficientes (novo time/liga)
""")
                    continue

                media_total = (
                    stats_home["media_feitos"]
                    + stats_home["media_sofridos"]
                    + stats_away["media_feitos"]
                    + stats_away["media_sofridos"]
                ) / 2

                prob = int(media_total * 25)

                oportunidades.append(f"""🔥 OPORTUNIDADE

{home} x {away}
✔️ Over 2.5 gols
📊 Probabilidade: {prob}%
""")

            except Exception as e:
                print("Erro jogo:", e)
                continue

    if not oportunidades:
        return ["🤖 Nenhum jogo encontrado hoje"]

    return oportunidades[:5]


async def enviar_alerta():
    jogos = buscar_jogos()

    mensagem = "📊 ANÁLISE DO DIA\n\n"

    for j in jogos:
        mensagem += j + "\n"

    try:
        await bot.send_message(chat_id=CHAT_ID, text=mensagem)
        print("✅ Enviado")
    except Exception as e:
        print("Erro Telegram:", e)


async def main():
    print("🚀 Bot rodando (ligas filtradas)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(120)


if __name__ == "__main__":
    asyncio.run(main())