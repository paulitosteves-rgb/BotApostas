import requests
import time
from datetime import datetime, timedelta, timezone

# ==============================
# CONFIG
# ==============================
TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "7729625060"

# ==============================
# CONTROLE DE ENVIO
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
# BUSCAR JOGOS (ESPN)
# ==============================
def buscar_jogos():
    print("🔍 Buscando jogos ESPN...")

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"
        res = requests.get(url, headers=headers, timeout=5)

        print("Status ESPN:", res.status_code)

        if res.status_code != 200:
            raise Exception("Erro na API")

        data = res.json()
        jogos = []

        for event in data.get("events", []):

            competitions = event.get("competitions", [])
            if not competitions:
                continue

            teams = competitions[0].get("competitors", [])
            if len(teams) < 2:
                continue

            home = teams[0]["team"]["name"]
            away = teams[1]["team"]["name"]

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

            jogos.append((jogo_id, home, away, hora))

        return jogos

    except Exception as e:
        print("⚠️ erro ESPN:", e)

    return []

# ==============================
# ANÁLISE (ESTRATÉGIA)
# ==============================
def analisar():

    jogos = buscar_jogos()
    entradas = []

    times_grandes = [
        "Barcelona", "Real Madrid", "Manchester City", "Liverpool",
        "Bayern Munich", "PSG", "Arsenal", "Chelsea",
        "Juventus", "Inter", "Milan",
        "Flamengo", "Palmeiras", "Atlético-MG"
    ]

    for jogo_id, home, away, hora in jogos:

        # evitar repetição
        if jogo_id in jogos_enviados:
            continue

        home_grande = any(t in home for t in times_grandes)
        away_grande = any(t in away for t in times_grandes)

        # 🔵 OVER 2.5 (FORTE)
        if home_grande and away_grande:
            msg = f"""🔥 OVER 2.5 (FORTE)

{home} x {away}
🕒 {hora}

📊 Duas equipes com perfil ofensivo
📈 Forte tendência de gols

💰 Sugestão: entrada simples
⚠️ Gestão: até 2% da banca
"""

        # 🟢 OVER 1.5 (BOM)
        elif home_grande or away_grande:
            msg = f"""🟢 OVER 1.5 (BOM)

{home} x {away}
🕒 {hora}

📊 Cenário propício para pelo menos 2 gols
📈 Tendência ofensiva consistente

💰 Sugestão: múltiplas ou entrada conservadora
⚠️ Gestão: 1 a 2% da banca
"""

        else:
            continue

        entradas.append((jogo_id, msg))

    return entradas

# ==============================
# LOOP PRINCIPAL
# ==============================
print("🚀 BOT INICIADO (MODO TIPSTER FINAL)")

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
        print("💥 ERRO LOOP:", e)

    time.sleep(600)