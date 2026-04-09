import requests
import time
from datetime import datetime, timedelta

# ================= CONFIG =================
TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "@Over_golsPV"

SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"

jogos_enviados = set()

# ================= TELEGRAM =================
def enviar_mensagem(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto}
    requests.post(url, data=payload)

# ================= HISTÓRICO =================
def pegar_historico_time(team_id):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/teams/{team_id}/schedule"
        response = requests.get(url)
        data = response.json()

        jogos = data.get("events", [])[:10]

        gols_marcados = 0
        gols_sofridos = 0
        total = 0

        for jogo in jogos:
            try:
                comps = jogo["competitions"][0]["competitors"]

                # 🔥 IGNORA JOGO SEM PLACAR
                if not comps[0].get("score") or not comps[1].get("score"):
                    continue

                for t in comps:
                    if t["team"]["id"] == team_id:
                        gols_marcados += int(t["score"])
                    else:
                        gols_sofridos += int(t["score"])

                total += 1

            except:
                continue

        if total == 0:
            return None

        return gols_marcados / total, gols_sofridos / total

    except:
        return None

# ================= CLASSIFICAÇÃO =================
def classificar(potencial):
    if potencial >= 3:
        return "🔥 FORTE (Over 2.5)"
    elif potencial >= 2:
        return "🟢 BOM (Over 1.5)"
    return None

# ================= LOOP =================
def rodar_bot():
    while True:
        try:
            response = requests.get(SCOREBOARD_URL)
            data = response.json()

            for evento in data.get("events", []):
                jogo_id = evento["id"]

                if jogo_id in jogos_enviados:
                    continue

                status = evento["status"]["type"]["description"]

                if status != "Scheduled":
                    continue

                liga = evento.get("league", {}).get("name", "")

                casa = evento["competitions"][0]["competitors"][0]
                fora = evento["competitions"][0]["competitors"][1]

                nome_casa = casa["team"]["name"]
                nome_fora = fora["team"]["name"]

                id_casa = casa["team"]["id"]
                id_fora = fora["team"]["id"]

                # 🔥 HISTÓRICO REAL
                hist_casa = pegar_historico_time(id_casa)
                hist_fora = pegar_historico_time(id_fora)

                if not hist_casa or not hist_fora:
                    continue

                gm_casa, gs_casa = hist_casa
                gm_fora, gs_fora = hist_fora

                # 🔥 CÁLCULO MELHORADO
                potencial = (gm_casa + gs_fora) + (gm_fora + gs_casa)

                print(f"{nome_casa} x {nome_fora} | Potencial: {potencial:.2f}")

                classificacao = classificar(potencial)

                if not classificacao:
                    continue

                mensagem = f"""
🚨 ENTRADA PRÉ-JOGO (ESTATÍSTICA)

{classificacao}

⚽ {nome_casa} x {nome_fora}
🏆 {liga}

📊 Ataque casa: {gm_casa:.2f}
📊 Defesa fora: {gs_fora:.2f}

📊 Ataque fora: {gm_fora:.2f}
📊 Defesa casa: {gs_casa:.2f}

🧠 Potencial: {potencial:.2f}

💰 Gestão: 1% a 2% da banca
"""

                enviar_mensagem(mensagem)
                jogos_enviados.add(jogo_id)

        except Exception as e:
            print("Erro:", e)

        time.sleep(600)

# ================= START =================
rodar_bot()