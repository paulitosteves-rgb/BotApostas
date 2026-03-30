import requests
import os
import asyncio
from datetime import datetime, timedelta
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
    headers = {"x-apisports-key": API_KEY}

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
# 📅 BUSCAR DATA COM JOGOS
# ==============================
def buscar_data_com_jogos():
    for i in range(3):  # hoje + próximos 2 dias
        data_teste = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")

        url = f"{BASE_URL}/fixtures?date={data_teste}"
        data = fazer_request(url)

        if data and data["response"]:
            print(f"📅 Usando data: {data_teste}")
            return data_teste, data

    return None, None


# ==============================
# 📊 BUSCAR JOGOS
# ==============================
def buscar_jogos():
    data_uso, data = buscar_data_com_jogos()

    if not data:
        return ["🤖 Nenhum jogo encontrado (API possivelmente instável)"]

    oportunidades = []
    fallback = []

    for jogo in data["response"][:20]:
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

            # 🔥 SEMPRE GUARDA COMO FALLBACK
            fallback.append((home, away))

            if not stats_home or not stats_away:
                continue

            media_total = (
                stats_home["media_feitos"]
                + stats_home["media_sofridos"]
                + stats_away["media_feitos"]
                + stats_away["media_sofridos"]
            ) / 2

            prob = int(media_total * 25)

            if media_total >= 1.6:
                oportunidades.append((prob, home, away))

        except Exception as e:
            print("Erro jogo:", e)
            continue

    # 🔥 PRIORIDADE: oportunidades reais
    if oportunidades:
        oportunidades.sort(reverse=True)
        return [f"""🔥 OPORTUNIDADE

{o[1]} x {o[2]}
✔️ Over 2.5 gols
📊 Probabilidade: {o[0]}%
""" for o in oportunidades[:5]]

    # 🔥 FALLBACK GARANTIDO
    if fallback:
        return [f"""📊 JOGOS ENCONTRADOS ({data_uso})

{f[0]} x {f[1]}
""" for f in fallback[:5]]

    return ["🤖 Nenhum jogo disponível"]


# ==============================
# 📲 TELEGRAM
# ==============================
async def enviar_alerta():
    jogos = buscar_jogos()

    mensagem = "📊 ANÁLISE AUTOMÁTICA\n\n"

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
    print("🚀 Bot rodando (anti-vazio total)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(120)


# ==============================
# ▶️ START
# ==============================
if __name__ == "__main__":
    asyncio.run(main())