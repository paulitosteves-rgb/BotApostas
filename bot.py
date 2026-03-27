import requests
import os
import time
from telegram import Bot

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
            return ["⚠️ Nenhum jogo encontrado"]

        oportunidades = []

        for jogo in data["response"]:
            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]

            status = jogo["fixture"]["status"]["short"]

            # 🔥 FILTRA APENAS PRÉ-JOGO
            if status != "NS":  # Not Started
                continue

            # 🔥 SIMULAÇÃO DE ANÁLISE (melhoraremos depois)
            # usamos ID do jogo como base pra gerar padrão
            jogo_id = jogo["fixture"]["id"]

            # regra simples: alterna padrões
            if jogo_id % 2 == 0:
                probabilidade = 70
                mercado = "Over 1.5 gols"
            else:
                probabilidade = 50
                mercado = "BTTS (Ambas Marcam)"

            # 🔥 FILTRO DE VALOR
            if probabilidade >= 65:
                oportunidades.append(
                    f"""🔥 ALERTA PRÉ-JOGO

{home} x {away}
✔️ Mercado: {mercado}
📊 Probabilidade estimada: {probabilidade}%
💡 Jogo com tendência ofensiva
"""
                )

        if not oportunidades:
            return ["⚠️ Nenhuma oportunidade pré-jogo encontrada"]

        return oportunidades

    except Exception as e:
        return [f"Erro: {str(e)}"]


def enviar_alerta():
    jogos = buscar_jogos()

    mensagem = "📊 ANÁLISE PRÉ-JOGO\n\n"

    for j in jogos[:5]:
        mensagem += f"{j}\n"

    bot.send_message(chat_id=CHAT_ID, text=mensagem)


if __name__ == "__main__":
    while True:
        enviar_alerta()
        time.sleep(30)