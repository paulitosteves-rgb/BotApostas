import requests
import asyncio
from telegram import Bot
from datetime import datetime

TOKEN = "SEU_TOKEN"
CHAT_ID = "SEU_CHAT_ID"
API_KEY = "SUA_API_KEY"

bot = Bot(token=TOKEN)

BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"

ultimos_jogos_enviados = set()


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

        # 🔥 GARANTE SEMPRE 3 RETORNOS
        if not isinstance(data, list):
            return [], [], set()

        hoje = datetime.utcnow().date()

        over15 = []
        over25 = []
        novos_jogos = set()

        for jogo in data:
            try:
                home = jogo.get("home_team")
                away = jogo.get("away_team")
                jogo_id = f"{home} x {away}"

                # filtro data
                commence_time = jogo.get("commence_time")
                if commence_time:
                    data_jogo = datetime.fromisoformat(commence_time.replace("Z", "")).date()
                    if data_jogo != hoje:
                        continue

                bookmakers = jogo.get("bookmakers", [])

                odd15 = None
                odd25 = None

                for book in bookmakers:
                    for market in book.get("markets", []):
                        if market.get("key") == "totals":
                            for outcome in market.get("outcomes", []):

                                if outcome.get("name") == "Over":
                                    if outcome.get("point") == 1.5:
                                        odd15 = outcome.get("price")
                                    elif outcome.get("point") == 2.5:
                                        odd25 = outcome.get("price")

                # 🔵 OVER 1.5
                if odd15 and 1.25 <= odd15 <= 1.38:
                    over15.append(f"""🔵 ENTRADA SEGURA

{home} x {away}
🎯 Over 1.5 gols
💰 Odd: {odd15}
📊 Stake: 2%
""")
                    novos_jogos.add(jogo_id)

                # 🟢 OVER 2.5
                if odd25 and 1.80 <= odd25 <= 2.50:

                    if odd25 >= 2.10:
                        nivel = "🟢 EV+ FORTE (Stake 1%)"
                    else:
                        nivel = "🟡 BOA (Stake 1.5%)"

                    over25.append(f"""{nivel}

{home} x {away}
🎯 Over 2.5 gols
💰 Odd: {odd25}
""")
                    novos_jogos.add(jogo_id)

            except Exception as e:
                print("Erro jogo:", e)

        return over15[:5], over25[:5], novos_jogos

    except Exception as e:
        print("Erro geral:", e)
        return [], [], set()  # 🔥 SEMPRE 3


async def enviar_alerta():
    global ultimos_jogos_enviados

    over15, over25, novos_jogos = buscar_jogos()

    if novos_jogos == ultimos_jogos_enviados:
        print("🔁 Sem novidades")
        return

    ultimos_jogos_enviados = novos_jogos

    msg = "💰 ESTRATÉGIA DO DIA\n\n"

    if over15:
        msg += "🔵 ENTRADAS SEGURAS (Over 1.5)\n\n"
        for j in over15:
            msg += j + "\n"

    if over25:
        msg += "\n🟢 ENTRADAS DE VALOR (Over 2.5)\n\n"
        for j in over25:
            msg += j + "\n"

    if not over15 and not over25:
        msg += "📊 Sem oportunidades hoje"

    await bot.send_message(chat_id=CHAT_ID, text=msg)


async def main():
    print("🚀 Bot rodando (modo lucrativo corrigido)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(600)


if __name__ == "__main__":
    asyncio.run(main())