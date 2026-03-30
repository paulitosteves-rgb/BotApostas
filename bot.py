import requests
import os
import asyncio
from datetime import datetime
from telegram import Bot
import time

# ==============================
# 🔐 CONFIG
# ==============================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_KEY")

bot = Bot(token=TOKEN)

team_cache = {}

BASE_URL = "https://v3.football.api-sports.io"


# ==============================
# 🔁 REQUEST COM RETRY
# ==============================
def fazer_request(url, tentativas=3):
    headers = {
        "x-apisports-key": API_KEY
    }

    for i in range(tentativas):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()

            if "response" in data:
                return data

            print(f"⚠️ Tentativa {i+1} falhou:", data)

        except Exception as e:
            print(f"Erro tentativa {i+1}:", e)

        time.sleep(2)

    return None


# ==============================
# 📊 STATS
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


# ==============================
# 📊 BUSCAR JOGOS
# ==============================
def buscar_jogos():
    data_hoje = datetime.now().strftime("%Y-%m-%d")

    url = f"{BASE_URL}/fixtures?date={data_hoje}"

    data = fazer_request(url)

    if not data:
        return ["🤖 API instável, tentando novamente depois"]

    oportunidades = []
    fallback = []

    for jogo in data["response"][:15]:
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

            if not stats_home or not stats_away:
                continue

            media_total = (
                stats_home["media_feitos"]
                + stats_home["media_sofridos"]
                + stats_away["media_feitos"]
                + stats_away["media_sofridos"]
            ) / 2

            prob = int(media_total * 25)

            fallback.append((prob, home, away, media_total))

            # 🔥 critério mais leve ainda
            if media_total >= 1.6:
                oportunidades.append((prob, home, away))

        except Exception as e:
            print("Erro jogo:", e)
            continue

    # 🔥 GARANTIR SINAL
    if not oportunidades:
        fallback.sort(reverse=True)
        oportunidades = fallback[:2]  # pega os 2 melhores

        return [f"""🔥 OPORTUNIDADE (FORÇADA)

{o[1]} x {o[2]}
✔️ Over 2.5 gols
📊 Probabilidade: {o[0]}%
""" for o in oportunidades]

    oportunidades.sort(reverse=True)

    return [f"""🔥 OPORTUNIDADE

{o[1]} x {o[2]}
✔️ Over 2.5 gols
📊 Probabilidade: {o[0]}%
""" for o in oportunidades[:5]]


# ==============================
# 📲 TELEGRAM
# ==============================
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


# ==============================
# 🔁 LOOP
# ==============================
async def main():
    print("🚀 Bot rodando (modo garantia de sinal)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(120)


# ==============================
# ▶️ START
# ==============================
if __name__ == "__main__":
    asyncio.run(main())