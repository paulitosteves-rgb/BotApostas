import requests
import os
import asyncio
from datetime import datetime
from telegram import Bot

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_KEY")

bot = Bot(token=TOKEN)

team_cache = {}


def get_team_stats(team_id):
    if team_id in team_cache:
        return team_cache[team_id]

    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=5"

    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if "response" not in data:
            return None

        gols_feitos = 0
        gols_sofridos = 0
        jogos = 0

        for jogo in data["response"]:
            home_id = jogo["teams"]["home"]["id"]
            away_id = jogo["teams"]["away"]["id"]

            gols_home = jogo["goals"]["home"]
            gols_away = jogo["goals"]["away"]

            if gols_home is None or gols_away is None:
                continue

            if team_id == home_id:
                gols_feitos += gols_home
                gols_sofridos += gols_away
            else:
                gols_feitos += gols_away
                gols_sofridos += gols_home

            jogos += 1

        if jogos == 0:
            return None

        stats = {
            "media_feitos": gols_feitos / jogos,
            "media_sofridos": gols_sofridos / jogos
        }

        team_cache[team_id] = stats
        return stats

    except:
        return None


def buscar_jogos():
    data_hoje = datetime.now().strftime("%Y-%m-%d")

    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={data_hoje}"

    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if "response" not in data:
            return ["Erro API"]

        oportunidades = []
        fallback = []

        for jogo in data["response"][:15]:
            status = jogo["fixture"]["status"]["short"]

            if status not in ["NS", "TBD"]:
                continue

            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            home_id = jogo["teams"]["home"]["id"]
            away_id = jogo["teams"]["away"]["id"]

            stats_home = get_team_stats(home_id)
            stats_away = get_team_stats(away_id)

            if not stats_home or not stats_away:
                continue

            media_total = (
                stats_home["media_feitos"]
                + stats_home["media_sofridos"]
                + stats_away["media_feitos"]
                + stats_away["media_sofridos"]
            ) / 2

            prob = int(media_total * 20)

            texto = f"""{home} x {away}
📊 Média total: {media_total:.2f}
"""

            fallback.append((prob, texto))

            if media_total >= 2.0:
                oportunidades.append((prob, f"""🔥 OPORTUNIDADE

{home} x {away}
✔️ Over 2.5
📊 Prob: {prob}%
"""))

        # 🔥 SE NÃO TEM OPORTUNIDADE → USA FALLBACK
        if not oportunidades:
            fallback.sort(reverse=True, key=lambda x: x[0])

            return [f"📊 MELHORES JOGOS DO DIA\n\n" +
                    "\n".join([f"{f[1]}" for f in fallback[:5]])]

        oportunidades.sort(reverse=True, key=lambda x: x[0])

        return [o[1] for o in oportunidades[:5]]

    except Exception as e:
        return [f"Erro: {str(e)}"]


async def enviar_alerta():
    jogos = buscar_jogos()

    mensagem = "📊 ANÁLISE DO DIA\n\n"

    for j in jogos:
        mensagem += j + "\n"

    await bot.send_message(chat_id=CHAT_ID, text=mensagem)


async def main():
    print("Bot rodando...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(120)


if __name__ == "__main__":
    asyncio.run(main())