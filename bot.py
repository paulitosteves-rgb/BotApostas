import requests
from telegram import Bot

TOKEN = "SEU_TOKEN_AQUI"
CHAT_ID = "SEU_CHAT_ID"

bot = Bot(token=TOKEN)

import requests
import os

def buscar_jogos():
    import requests
    import os

    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures?date=2026-03-27"

    headers = {
        "X-RapidAPI-Key": os.getenv("API_KEY"),
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        print("DEBUG API:", data)  # 👈 vai aparecer no Railway

        if "response" not in data or not data["response"]:
            return ["⚠️ Nenhum jogo encontrado ou erro na API"]

        jogos = []
        for jogo in data["response"]:
            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]
            jogos.append(f"{home} x {away}")

        return jogos

    except Exception as e:
        return [f"Erro geral: {str(e)}"]

def enviar_alerta():
    jogos = buscar_jogos()

    mensagem = "🔥 Jogos ao vivo hoje:\n\n"
    for j in jogos[:5]:
        mensagem += f"⚽ {j}\n"

    bot.send_message(chat_id=CHAT_ID, text=mensagem)

if __name__ == "__main__":
    enviar_alerta()