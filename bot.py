import requests
import os
import asyncio
from datetime import datetime
from telegram import Bot

# ==============================
# 🔐 CONFIG
# ==============================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_KEY")

bot = Bot(token=TOKEN)

# 🔥 CACHE
team_cache = {}

# ==============================
# 📊 BUSCAR ESTATÍSTICAS
# ==============================
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

        gols_feitos = 0
        gols_sofridos = 0
        jogos = 0

        if "response" not in data:
            return None

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

    except Exception as e:
        print("Erro stats:", e)
        return None


# ==============================
# 📊 BUSCAR JOGOS
# ==============================
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
            return ["Erro na API"]

        oportunidades = []

        jogos_lista = data["response"][:10]

        for jogo in jogos_lista:
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

                if media_total >= 2.8:
                    mercado = "Over 2.5 gols"
                    prob = min(int(media_total * 25), 85)

                elif (
                    stats_home["media_feitos"] >= 1.3
                    and stats_away["media_feitos"] >= 1.3
                ):
                    mercado = "BTTS"
                    prob = min(int((stats_home["media_feitos"] + stats_away["media_feitos"]) * 30), 80)

                else:
                    continue

                if prob >= 60:
                    oportunidades.append({
                        "msg": f"""🔥 ALERTA PROFISSIONAL

{home} x {away}
✔️ {mercado}
📊 Probabilidade: {prob}%

📈 {home}: {stats_home['media_feitos']:.2f}⚽ | {stats_home['media_sofridos']:.2f}
📈 {away}: {stats_away['media_feitos']:.2f}⚽ | {stats_away['media_sofridos']:.2f}
""",
                        "prob": prob
                    })

            except Exception as e:
                print("Erro jogo:", e)
                continue

        oportunidades.sort(key=lambda x: x["prob"], reverse=True)

        if not oportunidades:
            return ["🤖 Sem oportunidades no momento"]

        return [o["msg"] for o in oportunidades[:5]]

    except Exception as e:
        return [f"Erro geral: {str(e)}"]


# ==============================
# 📲 ENVIO (ASYNC)
# ==============================
async def enviar_alerta():
    jogos = buscar_jogos()

    mensagem = "📊 TOP OPORTUNIDADES DO DIA\n\n"

    for j in jogos:
        mensagem += j + "\n"

    try:
        await bot.send_message(chat_id=CHAT_ID, text=mensagem)
        print("✅ Mensagem enviada")
    except Exception as e:
        print("❌ Erro Telegram:", e)


# ==============================
# 🔁 LOOP PRINCIPAL ASYNC
# ==============================
async def main():
    print("🚀 Bot iniciado (async)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(30)


# ==============================
# ▶️ START
# ==============================
if __name__ == "__main__":
    asyncio.run(main())