import requests
import asyncio
from telegram import Bot
from datetime import datetime

# ==============================
# CONFIG
# ==============================
TOKEN = "SEU_TOKEN_TELEGRAM_AQUI"
CHAT_ID = "SEU_CHAT_ID_AQUI"
API_KEY = "SUA_API_KEY_AQUI"

bot = Bot(token=TOKEN)

BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"

# 🔥 CONTROLE DE DUPLICAÇÃO
ultimos_jogos_enviados = set()


# ==============================
# BUSCAR JOGOS
# ==============================
def buscar_jogos():
    global ultimos_jogos_enviados

    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "totals",
        "oddsFormat": "decimal"
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()

        if not isinstance(data, list):
            return [], ["Erro API"]

        entradas = []
        novos_jogos = set()

        hoje = datetime.utcnow().date()

        for jogo in data:
            try:
                home = jogo.get("home_team")
                away = jogo.get("away_team")

                jogo_id = f"{home} x {away}"

                # 🔥 FILTRO DE DATA (SÓ HOJE)
                commence_time = jogo.get("commence_time")
                if commence_time:
                    data_jogo = datetime.fromisoformat(commence_time.replace("Z", "")).date()
                    if data_jogo != hoje:
                        continue

                bookmakers = jogo.get("bookmakers", [])

                odd = None

                for book in bookmakers:
                    for market in book.get("markets", []):
                        if market.get("key") == "totals":
                            for outcome in market.get("outcomes", []):
                                if outcome.get("name") == "Over" and outcome.get("point") == 2.5:
                                    odd = outcome.get("price")
                                    break
                        if odd:
                            break
                    if odd:
                        break

                if not odd:
                    continue

                if 1.60 <= odd <= 2.50:

                    if odd >= 2.10:
                        nivel = "🟢 EV+ FORTE"
                    elif odd >= 1.85:
                        nivel = "🟡 BOA"
                    else:
                        nivel = "🔵 SEGURA"

                    entradas.append(f"""{nivel}

{home} x {away}
🎯 Over 2.5 gols
💰 Odd: {odd}
""")

                    novos_jogos.add(jogo_id)

            except Exception as e:
                print("Erro jogo:", e)

        return entradas[:10], novos_jogos

    except Exception as e:
        return [], [f"Erro: {str(e)}"]


# ==============================
# TELEGRAM
# ==============================
async def enviar_alerta():
    global ultimos_jogos_enviados

    entradas, novos_jogos = buscar_jogos()

    # 🔥 NÃO ENVIA SE FOR IGUAL AO ANTERIOR
    if novos_jogos == ultimos_jogos_enviados:
        print("🔁 Nenhuma mudança, não enviando alerta")
        return

    ultimos_jogos_enviados = novos_jogos

    if not entradas:
        return

    msg = "📊 OPORTUNIDADES DO DIA (FILTRADAS)\n\n"

    for e in entradas:
        msg += e + "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)


# ==============================
# LOOP
# ==============================
async def main():
    print("🚀 Bot rodando (modo profissional)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(600)


# ==============================
# START
# ==============================
if __name__ == "__main__":
    asyncio.run(main())