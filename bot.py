
import requests
import asyncio
from telegram import Bot
from datetime import datetime, UTC, timedelta

TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "7729625060"
API_KEY = "f941db0959abcf753ad321a81aa18a10"

bot = Bot(token=TOKEN)

LEAGUES = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_brazil_campeonato"
]

ultimos_jogos_enviados = set()

# ==============================
# BUSCAR JOGOS
# ==============================
def buscar_jogos():
    agora = datetime.now(UTC)
    limite = agora + timedelta(hours=12)

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

                    if jogo_id in novos_jogos:
                        continue

                    commence_time = jogo.get("commence_time")
                    if not commence_time:
                        continue

                    # 🔥 DATA EM UTC
                    data_jogo = datetime.fromisoformat(
                        commence_time.replace("Z", "+00:00")
                    )

                    # 🔥 FILTRO (PRÓXIMAS 12H)
                    if not (agora <= data_jogo <= limite):
                        continue

                    # 🔥 AJUSTE MANUAL BRASIL (-3H)
                    data_jogo_br = data_jogo - timedelta(hours=3)
                    hora_formatada = data_jogo_br.strftime("%H:%M")

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

                    # 🔵 OVER 1.5 (MAIS FLEXÍVEL)
                    if odd15 and 1.15 <= odd15 <= 1.60:
                        over15.append(f"""🔵 SEGURA

{home} x {away}
🕒 {hora_formatada}
🎯 Over 1.5
💰 {odd15}
📊 Stake: 2%
""")
                        novos_jogos.add(jogo_id)

                    # 🟢 OVER 2.5
                    if odd25 and 1.65 <= odd25 <= 3.00:

                        if odd25 >= 2.20:
                            nivel = "🟢 EV+ FORTE (1%)"
                        elif odd25 >= 1.90:
                            nivel = "🟡 BOA (1.5%)"
                        else:
                            nivel = "🔵 MODERADA (2%)"

                        over25.append(f"""{nivel}

{home} x {away}
🕒 {hora_formatada}
🎯 Over 2.5
💰 {odd25}
""")
                        novos_jogos.add(jogo_id)

                except Exception as e:
                    print("Erro jogo:", e)

        except Exception as e:
            print("Erro liga:", league, e)

    return over15[:8], over25[:8], novos_jogos


# ==============================
# TELEGRAM
# ==============================
async def enviar_alerta():
    global ultimos_jogos_enviados

    over15, over25, novos_jogos = buscar_jogos()

    if novos_jogos == ultimos_jogos_enviados:
        print("🔁 Sem novidades")
        return

    ultimos_jogos_enviados = novos_jogos

    msg = "💰 OPORTUNIDADES (PRÓXIMAS HORAS)\n\n"

    if over15:
        msg += "🔵 SEGURAS (Over 1.5)\n\n"
        for j in over15:
            msg += j + "\n"

    if over25:
        msg += "\n🟢 VALOR (Over 2.5)\n\n"
        for j in over25:
            msg += j + "\n"

    if not over15 and not over25:
        msg += "📊 Nenhuma entrada nas próximas horas"

    await bot.send_message(chat_id=CHAT_ID, text=msg)


# ==============================
# LOOP
# ==============================
async def main():
    print("🚀 Bot rodando (estável e otimizado)...")

    while True:
        await enviar_alerta()
        await asyncio.sleep(600)


# ==============================
# START
# ==============================
if __name__ == "__main__":
    asyncio.run(main())