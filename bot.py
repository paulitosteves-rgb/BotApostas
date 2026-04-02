import requests
import time

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

            data_str = event.get("date", "")
            hora = data_str[11:16] if data_str else "??:??"

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
# ANALISAR
# ==============================
def analisar():

    jogos = buscar_jogos()
    entradas = []

    for home, away, hora in jogos:

        entradas.append(f"""🟡 JOGO

{home} x {away}
🕒 {hora}

📊 Monitoramento ativo
""")

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