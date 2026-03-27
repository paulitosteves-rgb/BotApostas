import requests
import os
import time
from telegram import Bot

# 🔐 Variáveis do Railway
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_KEY")

bot = Bot(token=TOKEN)


def buscar_jogos():
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures?date=2026-03-27"

    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        print("DEBUG API:", data)

        if "response" not in data or not data["response"]:
            return ["⚠️ Nenhum jogo encontrado ou erro na API"]

        jogos = []

        for jogo in data["response"]:
            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            gols_home = jogo["goals"]["home"]
            gols_away = jogo["goals"]["away"]

            # evita erro se não tiver gols ainda
            if gols_home is None or gols_away is None:
                continue

            total_gols = gols_home + gols_away

            # 🔥 FILTRO DE OPORTUNIDADE
            if total_gols >= 2:
                jogos.append(
                    f"""🔥 OPORTUNIDADE

{home} x {away}
✔️ Tendência Over 2.5
⚽ Gols atuais: {total_gols}
"""
                )

        if not jogos:
            return ["⚠️ Nenhuma oportunidade encontrada hoje"]

        return jogos

    except Exception as e:
        return [f"Erro geral: {str(e)}"]


def enviar_alerta():
    jogos = buscar_jogos()

    mensagem = "🔥 ALERTAS DO DIA\n\n"

    for j in jogos[:5]:
        mensagem += f"{j}\n"

    bot.send_message(chat_id=CHAT_ID, text=mensagem)


# 🔁 LOOP AUTOMÁTICO (RODA 24H)
if __name__ == "__main__":
    while True:
        enviar_alerta()
        time.sleep(3600)  # executa a cada 1 hora