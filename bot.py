import requests
import time
from datetime import datetime, timedelta, timezone

# ==============================
# CONFIG
# ==============================
TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "7729625060"

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
# BUSCAR JOGOS (ESPN REAL)
# ==============================
def buscar_jogos():
    print("🔍 Buscando jogos ESPN...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    }

    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"

        res = requests.get(url, headers=headers, timeout=5)

        print("Status ESPN:", res.status_code)

        if res.status_code != 200:
            raise Exception("Status diferente de 200")

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
            # AJUSTE DE HORÁRIO (UTC → BR)
            # ==============================
            data_str = event.get("date", "")

            if data_str:
                data_utc = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
                data_br = data_utc.astimezone(timezone(timedelta(hours=-3)))
                hora = data_br.strftime("%H:%M")
            else:
                hora = "??:??"

            jogos.append((home, away, hora))

        if jogos:
            print(f"✅ {len(jogos)} jogos encontrados")
            return jogos[:20]

    except Exception as e:
        print("⚠️ erro ESPN:", e)

    # ==============================
    # FALLBACK
    # ==============================
    print("⚠️ fallback ativado")

    return [
        ("Time A", "Time B", "16:00"),
        ("Time C", "Time D", "18:00"),
        ("Time E", "Time F", "20:00"),
    ]

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

    for home, away, hora in jogos:

        home_grande = any(t in home for t in times_grandes)
        away_grande = any(t in away for t in times_grandes)

        # 🔵 OVER 2.5 FORTE
        if home_grande and away_grande:
            entradas.append(f"""🔵 OVER 2.5 (FORTE)

{home} x {away}
🕒 {hora}

📊 Duas equipes ofensivas
""")

        # 🟢 OVER 1.5 BOM
        elif home_grande or away_grande:
            entradas.append(f"""🟢 OVER 1.5 (BOM)

{home} x {away}
🕒 {hora}

📊 Um time forte em campo
""")

        # 🟡 EVITAR
        else:
            continue

    return entradas

# ==============================
# LOOP PRINCIPAL
# ==============================
print("🚀 BOT INICIADO (MODO ESTÁVEL FINAL)")

while True:
    try:
        entradas = analisar()

        msg = "📊 JOGOS DO DIA\n\n"

        for e in entradas:
            msg += e + "\n"

        print("📤 Enviando mensagem...")
        enviar(msg)

    except Exception as e:
        print("💥 ERRO LOOP:", e)

    time.sleep(600)  # 10 minutos