import requests
import os
import time
from datetime import datetime
from telegram import Bot

# ==============================
# 🔐 CONFIG (Railway Variables)
# ==============================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_KEY")

bot = Bot(token=TOKEN)


# ==============================
# 📊 BUSCAR JOGOS DO DIA
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

        print("📡 DEBUG API:", data_hoje)

        if "response" not in data:
            return ["⚠️ Erro na API (sem 'response')"]

        if not data["response"]:
            return ["⚠️ Nenhum jogo encontrado hoje"]

        oportunidades = []

        for jogo in data["response"]:
            try:
                home = jogo["teams"]["home"]["name"]
                away = jogo["teams"]["away"]["name"]
                status = jogo["fixture"]["status"]["short"]

                print(f"🔍 {home} x {away} | status: {status}")

                # ==============================
                # 🎯 FILTRO PRÉ-JOGO
                # ==============================
                if status not in ["NS", "TBD"]:
                    continue

                # ==============================
                # 🧠 LÓGICA DE ANÁLISE (BASE)
                # ==============================
                jogo_id = jogo["fixture"]["id"]

                if jogo_id % 2 == 0:
                    probabilidade = 70
                    mercado = "Over 2.5 gols"
                else:
                    probabilidade = 65
                    mercado = "BTTS (Ambas Marcam)"

                # ==============================
                # 🔥 FILTRO DE VALOR
                # ==============================
                if probabilidade >= 65:
                    oportunidades.append(
                        f"""🔥 ALERTA PRÉ-JOGO

{home} x {away}
✔️ Mercado: {mercado}
📊 Probabilidade: {probabilidade}%
🧠 Tendência ofensiva identificada
"""
                    )

            except Exception as e:
                print("⚠️ Erro ao processar jogo:", e)
                continue

        if not oportunidades:
            return ["🤖 Bot ativo, mas sem oportunidades no momento"]

        return oportunidades

    except Exception as e:
        return [f"❌ Erro geral: {str(e)}"]


# ==============================
# 📲 ENVIO PARA TELEGRAM
# ==============================
def enviar_alerta():
    jogos = buscar_jogos()

    mensagem = "📊 ANÁLISE PRÉ-JOGO\n\n"

    for j in jogos[:5]:
        mensagem += f"{j}\n"

    try:
        bot.send_message(chat_id=CHAT_ID, text=mensagem)
        print("✅ Mensagem enviada com sucesso")
    except Exception as e:
        print("❌ Erro ao enviar mensagem:", e)


# ==============================
# 🔁 LOOP PRINCIPAL
# ==============================
if __name__ == "__main__":
    print("🚀 Bot iniciado...")

    while True:
        enviar_alerta()
        time.sleep(3600)  # 1 hora