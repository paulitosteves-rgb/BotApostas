import requests
import time
from datetime import datetime, timedelta

# ================= CONFIG =================
TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "@Over_golsPV"

LIGAS_VALIDAS = [
    "Brazil", "Premier League", "La Liga", "Bundesliga",
    "Serie A", "Ligue 1", "Eredivisie", "MLS",
    "Argentina", "Portugal", "Belgium", "Turkey", "Denmark",

    # 🔥 COMPETIÇÕES EUROPEIAS
    "Champions League",
    "Europa League",
    "Conference League"
]

jogos_enviados = set()

# ================= TELEGRAM =================
def enviar_mensagem(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": texto,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

# ================= STATS (SUMMARY) =================
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

    # Volume (leve)
    if stats["shots"] >= 6:
        score += 2
    if stats["shots_on_target"] >= 2:
        score += 2

    # Pressão
    if stats["possession"] > 55:
        score += 1

    # Liga ofensiva
    if any(l in liga for l in ["Eredivisie", "MLS", "Belgium", "Turkey"]):
        score += 1

    # Momento
    if 10 <= minuto <= 40:
        score += 1
    if 50 <= minuto <= 80:
        score += 1

    # Empurrão (volume)
    if stats["shots"] == 0:
        score += 1

    return score

# ================= CLASSIFICAÇÃO =================
def classificar(score):
    if score >= 3:
        return "🔥 FORTE (Over 2.5)"
    elif score >= 1:
        return "🟢 TESTE (Over 1.5)"
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

                # DEBUG opcional (pode remover depois)
                # print("Liga detectada:", liga)

                if not any(l in liga for l in LIGAS_VALIDAS):
                    continue

                jogo_id = evento["id"]

                if jogo_id in jogos_enviados:
                    continue

                status = evento["status"]["type"]["detail"]

                if "min" not in status:
                    continue

                minuto = int(''.join(filter(str.isdigit, status)))

                if minuto < 10:
                    continue

                nome_casa = evento["competitions"][0]["competitors"][0]["team"]["name"]
                nome_fora = evento["competitions"][0]["competitors"][1]["team"]["name"]

                stats = pegar_stats_summary(jogo_id)

                if not stats:
                    stats = {
                        "shots": 0,
                        "shots_on_target": 0,
                        "possession": 50
                    }

                score = calcular_score(stats, minuto, liga)
                classificacao = classificar(score)

                # DEBUG
                print(f"{nome_casa} x {nome_fora} | {liga} | Min: {minuto} | Stats: {stats} | Score: {score}")

                if not classificacao:
                    continue

                mensagem = f"""
<b>🧪 ENTRADA EM TESTE</b>

{classificacao}

⚽ {nome_casa} x {nome_fora}
🏆 {liga}
⏱️ {minuto} min

📊 Finalizações: {stats['shots']}
🎯 No gol: {stats['shots_on_target']}
📈 Posse: {stats['possession']}%

🧠 Score: {score}

⚠️ <b>Modo observação ativo</b>
"""

                oportunidades.append((score, mensagem, jogo_id))

            # 🔥 Top 6 (mais volume)
            top = sorted(oportunidades, key=lambda x: x[0], reverse=True)[:6]

            for score, msg, jogo_id in top:
                enviar_mensagem(msg)
                jogos_enviados.add(jogo_id)

            print(f"🔁 Loop executado - {len(top)} sinais enviados")

        except Exception as e:
            print("Erro:", e)

        time.sleep(600)

# ================= START =================
rodar_bot()
