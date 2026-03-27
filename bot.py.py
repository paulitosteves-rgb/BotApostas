import requests
from telegram import Bot

TOKEN = "SEU_TOKEN_AQUI"
CHAT_ID = "SEU_CHAT_ID"

bot = Bot(token=TOKEN)

def buscar_jogos():
    # API gratuita de exemplo (pode trocar depois)
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures?live=all"

    headers = {
        "X-RapidAPI-Key": "SUA_API_KEY",
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    jogos = []

    for jogo in data["response"]:
        home = jogo["teams"]["home"]["name"]
        away = jogo["teams"]["away"]["name"]

        jogos.append(f"{home} x {away}")

    return jogos

def enviar_alerta():
    jogos = buscar_jogos()

    mensagem = "🔥 Jogos ao vivo hoje:\n\n"
    for j in jogos[:5]:
        mensagem += f"⚽ {j}\n"

    bot.send_message(chat_id=CHAT_ID, text=mensagem)

if __name__ == "__main__":
    enviar_alerta()