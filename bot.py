import requests
import os
import asyncio
from datetime import datetime, timedelta
from telegram import Bot
import time

# ==============================
# CONFIG
# ==============================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_KEY")

bot = Bot(token=TOKEN)

BASE_URL = "https://v3.football.api-sports.io"
team_cache = {}


# ==============================
# REQUEST
# ==============================
def fazer_request(url, tentativas=3):
    headers = {"x-apisports-key": API_KEY}

    for _ in range(tentativas):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()

            if "response" in data:
                return data

        except:
            pass

        time.sleep(2)

    return None


# ==============================
# STATS
# ==============================
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


# ==============================
# BUSCAR DATA
# ==============================
def buscar_data():
    for i in range(3):
        data_teste = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")

        url = f"{BASE_URL}/fixtures?date={data_teste}"
        data = fazer_request(url)

        if data and data["response"]:
            return data_teste, data

    return None, None


# ==============================
# ANALISAR JOGOS
# ==============================
def buscar_jogos():
    data_uso, data = buscar_data()

    if not data:
        return ["🤖 API sem retorno no momento"]

    resultados = []

    for jogo in data["response"][:10]:
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

            # 🔥 COM STATS
            if stats_home and stats_away:
                media_total = (
                    stats_home["media_feitos"]
                    + stats_home["media_sofridos"]
                    + stats_away["media_feitos"]
                    + stats_away["media_sofridos"]
                ) / 2

                prob = int(media_total * 25)

                resultados.append(f"""🔥 OPORTUNIDADE

{home} x {away}
✔️ Over 2.5 gols
📊 Probabilidade: {prob}%

📈 {home}: {stats_home['media_feitos']:.2f}⚽
📈 {away}: {stats_away['media_feitos']:.2f}⚽
""")

            # 🔥 SEM STATS (fallback inteligente)
            else:
                resultados.append(f"""📊 JOGO DO DIA

{home} x {away}
⚠️ Dados insuficientes (novo time/liga)
💡 Possível oportunidade ao vivo
""")

        except Exception as e:
            print("Erro:", e)
            continue

    if not resultados:
        return ["🤖 Nenhum jogo analisável"]

    return resultados[:5]


# ==============================
# TELEGRAM
# ==============================
async def enviar_alerta():
    jogos = buscar_jogos()

    mensagem = "📊 ANÁLISE DO DIA\n\n"

    for j in jogos:
        mensagem += j + "\n"

    await bot.send_message(chat_id=CHAT_ID, text=mensagem)


# ==============================
# LOOP
# ==============================
async def main():
    print("🚀 Bot rodando (modo inteligente)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(120)


# ==============================
# START
# ==============================
if __name__ == "__main__":
    asyncio.run(main())