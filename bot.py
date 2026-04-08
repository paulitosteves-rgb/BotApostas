import requests
import time
from datetime import datetime, timedelta

# ================= CONFIG =================
TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "@Over_golsPV"

SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"
SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/summary?event="

LIGAS_VALIDAS = [
    "Brazil", "Premier League", "La Liga", "Bundesliga",
    "Serie A", "Ligue 1", "Eredivisie", "MLS",
    "Argentina", "Portugal", "Belgium", "Turkey", "Denmark"
]

jogos_enviados = set()

# ================= TELEGRAM =================
def enviar_mensagem(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto}
    requests.post(url, data=payload)

# ================= SUMMARY STATS =================
def pegar_stats_summary(event_id):
    try:
        response = requests.get(SUMMARY_URL + event_id)
        data = response.json()

        teams = data["boxscore"]["teams"]

        def get_stat(team, nome):
            for s in team["statistics"]:
                if s["name"] == nome:
                    return float(s["displayValue"])
            return 0

        shots = get_stat(teams[0], "shotsTotal") + get_stat(teams[1], "shotsTotal")
        shots_on_target = get_stat(teams[0], "shotsOnTarget") + get_stat(teams[1], "shotsOnTarget")

        possession_home = get_stat(teams[0], "possession")
        possession_away = get_stat(teams[1], "possession")

        possession = max(possession_home, possession_away)

        return {
            "shots": shots,
            "shots_on_target": shots_on_target,
            "possession": possession
        }

    except:
        return None

# ================= SCORE =================
def calcular_score(stats, minuto, liga):
    score = 0

    # Volume real
    if stats["shots"] >= 10:
        score += 2
    if stats["shots_on_target"] >= 5:
        score += 3

    # Pressão real
    if stats["possession"] > 60:
        score += 1

    # Liga ofensiva
    if any(l in liga for l in ["Eredivisie", "MLS", "Belgium", "Turkey"]):
        score += 1

    # Momento ideal
    if 20 <= minuto <= 40:
        score += 2
    if 55 <= minuto <= 75:
        score += 2

    return score

# ================= CLASSIFICAÇÃO =================
def classificar(score):
    if score >= 6:
        return "🔥 FORTE (Over 2.5)"
    elif score >= 4:
        return "🟢 BOM (Over 1.5)"
    return None

# ================= LOOP =================
def rodar_bot():
    while True:
        try:
            response = requests.get(SCOREBOARD_URL)
            data = response.json()

            oportunidades = []

            for evento in data.get("events", []):
                liga = evento.get("league", {}).get("name", "")

                if not any(l in liga for l in LIGAS_VALIDAS):
                    continue

                jogo_id = evento["id"]

                if jogo_id in jogos_enviados:
                    continue

                status = evento["status"]["type"]["detail"]

                if "min" not in status:
                    continue

                minuto = int(''.join(filter(str.isdigit, status)))

                if minuto < 20:
                    continue

                nome_casa = evento["competitions"][0]["competitors"][0]["team"]["name"]
                nome_fora = evento["competitions"][0]["competitors"][1]["team"]["name"]

                # 🔥 AQUI ESTÁ O DIFERENCIAL
                stats = pegar_stats_summary(jogo_id)

                if not stats:
                    continue

                score = calcular_score(stats, minuto, liga)
                classificacao = classificar(score)

                print(f"{nome_casa} x {nome_fora} | Min: {minuto} | Stats: {stats} | Score: {score}")

                if not classificacao:
                    continue

                mensagem = f"""
🚨 ENTRADA PREMIUM

{classificacao}

⚽ {nome_casa} x {nome_fora}
⏱️ {minuto} min

📊 Finalizações: {stats['shots']}
🎯 No gol: {stats['shots_on_target']}
📈 Posse: {stats['possession']}%

🧠 Score: {score}

💰 Entrada de valor detectada
⚠️ Gestão: 1% a 2% da banca
"""

                oportunidades.append((score, mensagem, jogo_id))

            # TOP 3
            top = sorted(oportunidades, key=lambda x: x[0], reverse=True)[:3]

            for score, msg, jogo_id in top:
                enviar_mensagem(msg)
                jogos_enviados.add(jogo_id)

            print(f"🔁 Loop executado - {len(top)} sinais PREMIUM enviados")

        except Exception as e:
            print("Erro:", e)

        time.sleep(600)

# ================= START =================
rodar_bot()