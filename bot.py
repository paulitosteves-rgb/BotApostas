import requests
import asyncio
from telegram import Bot
from datetime import datetime

TOKEN = "SEU_TOKEN"
CHAT_ID = "SEU_CHAT_ID"
API_KEY = "SUA_API_KEY"

bot = Bot(token=TOKEN)

# 🔥 MULTI LIGAS
LEAGUES = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_brazil_campeonato"
]

ultimos_jogos_enviados = set()


def buscar_jogos():
    hoje = datetime.utcnow().date()

    over15 = []
    over25 = []
    novos_jogos = set()

    for league in LEAGUES:

        url = f"https://api.the-odds-api.com/v4/sports/{league}/odds"

        params = {
            "apiKey": API_KEY,
            "regions": "eu",
            "markets": "totals",
            "oddsFormat": "decimal"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if not isinstance(data, list):
                continue

            for jogo in data:
                try:
                    home = jogo.get("home_team")
                    away = jogo.get("away_team")

                    jogo_id = f"{home} x {away}"

                    # 🔥 evita duplicação entre ligas
                    if jogo_id in novos_jogos:
                        continue

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

                    # 🔵 OVER 1.5 (mais volume)
                    if odd15 and 1.20 <= odd15 <= 1.40:
                        over15.append(f"""🔵 SEGURA

{home} x {away}
🎯 Over 1.5
💰 {odd15}
📊 Stake: 2%
""")
                        novos_jogos.add(jogo_id)

                    # 🟢 OVER 2.5
                    if odd25 and 1.70 <= odd25 <= 2.80:

                        if odd25 >= 2.20:
                            nivel = "🟢 EV+ FORTE (1%)"
                        elif odd25 >= 1.90:
                            nivel = "🟡 BOA (1.5%)"
                        else:
                            nivel = "🔵 MODERADA (2%)"

                        over25.append(f"""{nivel}

{home} x {away}
🎯 Over 2.5
💰 {odd25}
""")
                        novos_jogos.add(jogo_id)

                except Exception as e:
                    print("Erro jogo:", e)

        except Exception as e:
            print("Erro liga:", league, e)

    return over15[:7], over25[:7], novos_jogos


async def enviar_alerta():
    global ultimos_jogos_enviados

    over15, over25, novos_jogos = buscar_jogos()

    if novos_jogos == ultimos_jogos_enviados:
        print("🔁 Sem novidades")
        return

    ultimos_jogos_enviados = novos_jogos

    msg = "💰 OPORTUNIDADES MULTI-LIGAS\n\n"

    if over15:
        msg += "🔵 SEGURAS (Over 1.5)\n\n"
        for j in over15:
            msg += j + "\n"

    if over25:
        msg += "\n🟢 VALOR (Over 2.5)\n\n"
        for j in over25:
            msg += j + "\n"

    if not over15 and not over25:
        msg += "📊 Sem oportunidades"

    await bot.send_message(chat_id=CHAT_ID, text=msg)


async def main():
    print("🚀 Bot rodando (multi-ligas ativado)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(600)


if __name__ == "__main__":
    asyncio.run(main())