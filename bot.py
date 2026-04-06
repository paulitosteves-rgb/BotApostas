import requests
import time
from datetime import datetime, timedelta, timezone

# ==============================
# CONFIG
# ==============================
TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "7729625060"

# ==============================
# CONTROLE
# ==============================
jogos_enviados = set()

# ==============================
# TELEGRAM
# ==============================
def enviar(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except Exception as e:
        print("Erro Telegram:", e)

# ==============================
# BUSCAR JOGOS ESPN
# ==============================
def buscar_jogos():
    print("🔍 Buscando jogos...")

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"
        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code != 200:
            return []

        data = res.json()
        jogos = []

        for event in data.get("events", []):

            competitions = event.get("competitions", [])
            if not competitions:
                continue

            comp = competitions[0]

            teams = comp.get("competitors", [])
            if len(teams) < 2:
                continue

            home = teams[0]["team"]["name"]
            away = teams[1]["team"]["name"]

            # ==============================
            # LIGA
            # ==============================
            liga = event.get("league", {}).get("name", "")

            ligas_boas = [
                "Premier League", "La Liga", "Bundesliga",
                "Serie A", "Ligue 1",
                "Eredivisie", "Primeira Liga",
                "MLS", "A-League",
                "Brasileirão", "Argentina"
            ]

            if not any(l.lower() in liga.lower() for l in ligas_boas):
                continue

            # ==============================
            # HORÁRIO BR
            # ==============================
            data_str = event.get("date", "")

            if data_str:
                data_utc = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
                data_br = data_utc.astimezone(timezone(timedelta(hours=-3)))
                hora = data_br.strftime("%H:%M")
            else:
                hora = "??:??"

            jogo_id = f"{home} x {away}"

            jogos.append((jogo_id, home, away, hora, liga))

        print(f"📊 Jogos filtrados: {len(jogos)}")
        return jogos

    except Exception as e:
        print("Erro ESPN:", e)
        return []

# ==============================
# ANÁLISE INTELIGENTE
# ==============================
def analisar():

    jogos = buscar_jogos()
    entradas = []

    times_grandes = [
        "Barcelona", "Real Madrid", "Manchester City", "Liverpool",
        "Bayern", "PSG", "Arsenal", "Chelsea",
        "Juventus", "Inter", "Milan",
        "Flamengo", "Palmeiras", "Atlético"
    ]

    ligas_over = ["Eredivisie", "A-League", "MLS"]

    for jogo_id, home, away, hora, liga in jogos:

        if jogo_id in jogos_enviados:
            continue

        home_grande = any(t.lower() in home.lower() for t in times_grandes)
        away_grande = any(t.lower() in away.lower() for t in times_grandes)

        # ==============================
        # 🔵 OVER 2.5 (VALOR REAL)
        # ==============================
        if home_grande and away_grande:

            msg = f"""🔥 OVER 2.5 (FORTE)

{home} x {away}
🕒 {hora}

📊 Confronto entre equipes ofensivas
📈 Alta probabilidade de gols

💰 Entrada recomendada: simples
⚠️ Gestão: até 2% da banca
"""

        # ==============================
        # 🟢 OVER 1.5 (BOM)
        # ==============================
        elif home_grande != away_grande:

            msg = f"""🟢 OVER 1.5 (BOM)

{home} x {away}
🕒 {hora}

📊 Cenário favorável para gols
📈 Tendência ofensiva consistente

💰 Entrada recomendada: múltiplas
⚠️ Gestão: 1 a 2% da banca
"""

        # ==============================
        # 🟡 OVER 1.5 (MODERADO)
        # ==============================
        elif any(l.lower() in liga.lower() for l in ligas_over):

            msg = f"""🟡 OVER 1.5 (MODERADO)

{home} x {away}
🕒 {hora}

📊 Liga com alta média de gols
📈 Forte padrão de over

💰 Entrada recomendada: múltiplas
⚠️ Gestão: até 1% da banca
"""

        else:
            continue

        entradas.append((jogo_id, msg))

    return entradas

# ==============================
# LOOP PRINCIPAL
# ==============================
print("🚀 BOT RODANDO (VERSÃO FINAL REFINADA)")

while True:
    try:
        entradas = analisar()

        if not entradas:
            print("🔁 Sem oportunidades")
            time.sleep(600)
            continue

        for jogo_id, msg in entradas:

            print(f"📤 Enviando: {jogo_id}")

            enviar(f"🚨 ENTRADA LIBERADA\n\n{msg}")

            jogos_enviados.add(jogo_id)

            time.sleep(2)

    except Exception as e:
        print("Erro geral:", e)

    time.sleep(600)