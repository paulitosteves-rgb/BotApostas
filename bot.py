import requests
import time
from datetime import datetime, timedelta

# ================= CONFIG =================
TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "7729625060"

URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"

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

# ================= SCORE =================
def calcular_score(stats, minuto, liga):
    score = 0

    shots = stats["shots"]
    shots_on_target = stats["shots_on_target"]
    possession = stats["possession"]

    # Volume
    if shots >= 8:
        score += 2
    if shots_on_target >= 3:
        score += 2

    # Pressão
    if possession > 55:
        score += 1

    # Liga ofensiva
    if any(l in liga for l in ["Eredivisie", "MLS", "Belgium", "Turkey"]):
        score += 1

    # Momento
    if 15 <= minuto <= 35:
        score += 1
    if 55 <= minuto <= 75:
        score += 2

    return score

# ================= CLASSIFICAÇÃO =================
def classificar(score):
    if score >= 4:
        return "🔥 FORTE (Over 2.5)"
    elif score >= 2:
        return "🟢 BOM (Over 1.5)"
    return None

# ================= STATS =================
def extrair_stats(evento):
    try:
        competitors = evento["competitions"][0]["competitors"]

        stats_home = competitors[0].get("statistics", [])
        stats_away = competitors[1].get("statistics", [])

        def get_stat(stats, nome):
            for s in stats:
                if s["name"] == nome:
                    return float(s["displayValue"])
            return 0

        shots = get_stat(stats_home, "shotsTotal") + get_stat(stats_away, "shotsTotal")
        shots_on_target = get_stat(stats_home, "shotsOnTarget") + get_stat(stats_away, "shotsOnTarget")

        possession_home = get_stat(stats_home, "possession")
        possession_away = get_stat(stats_away, "possession")

        possession = max(possession_home, possession_away)

        return {
            "shots": shots,
            "shots_on_target": shots_on_target,
            "possession": possession
        }

    except:
        return None

# ================= LOOP =================
def rodar_bot():
    while True:
        try:
            response = requests.get(URL)
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

                if minuto < 15:
                    continue

                nome_casa = evento["competitions"][0]["competitors"][0]["team"]["name"]
                nome_fora = evento["competitions"][0]["competitors"][1]["team"]["name"]

                stats = extrair_stats(evento)

                # 🔥 fallback (não ignora jogo)
                if not stats:
                    stats = {
                        "shots": 0,
                        "shots_on_target": 0,
                        "possession": 50
                    }

                score = calcular_score(stats, minuto, liga)
                classificacao = classificar(score)

                # DEBUG
                print(f"{nome_casa} x {nome_fora} | Min: {minuto} | Stats: {stats} | Score: {score}")

                if not classificacao:
                    continue

                mensagem = f"""
🚨 ENTRADA LIBERADA

{classificacao}

⚽ {nome_casa} x {nome_fora}
⏱️ {minuto} min

📊 Finalizações: {stats['shots']}
🎯 No gol: {stats['shots_on_target']}
📈 Posse: {stats['possession']}%

🧠 Score: {score}

💰 Gestão: 1% a 2% da banca
"""

                oportunidades.append((score, mensagem, jogo_id))

            # TOP 3
            top = sorted(oportunidades, key=lambda x: x[0], reverse=True)[:3]

            for score, msg, jogo_id in top:
                enviar_mensagem(msg)
                jogos_enviados.add(jogo_id)

            print(f"🔁 Loop executado - {len(top)} sinais enviados")

        except Exception as e:
            print("Erro:", e)

        time.sleep(600)

# ================= START =================
rodar_bot()