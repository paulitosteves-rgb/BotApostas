import requests
import time
from datetime import datetime, timedelta, timezone

# ==============================
# CONFIG
# ==============================
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

# ================= SCORE INTELIGENTE =================
def calcular_score(stats, minuto, liga):
    score = 0

    shots = stats.get("shots", 0)
    shots_on_target = stats.get("shots_on_target", 0)
    possession = stats.get("possession", 50)

    # Volume de jogo
    if shots >= 10:
        score += 2
    if shots_on_target >= 5:
        score += 2

    # Pressão
    if possession > 55:
        score += 1

    # Liga ofensiva
    if liga in ["Eredivisie", "MLS", "Belgium", "Turkey"]:
        score += 1

    # Momento do jogo
    if 20 <= minuto <= 35:
        score += 1
    if 55 <= minuto <= 70:
        score += 2

    return score

# ================= CLASSIFICAÇÃO =================
def classificar(score):
    if score >= 6:
        return "🔥 FORTE (Over 2.5)"
    elif score >= 4:
        return "🟢 BOM (Over 1.5)"
    else:
        return None

# ================= EXTRAÇÃO DE STATS =================
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
        return {}

# ================= LOOP PRINCIPAL =================
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

                # Filtro de tempo
                if minuto < 20:
                    continue

                nome_casa = evento["competitions"][0]["competitors"][0]["team"]["name"]
                nome_fora = evento["competitions"][0]["competitors"][1]["team"]["name"]

                stats = extrair_stats(evento)

                if not stats:
                    continue

                score = calcular_score(stats, minuto, liga)
                classificacao = classificar(score)

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

            # ================= TOP 3 =================
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