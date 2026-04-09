import requests
import time
from datetime import datetime, timedelta

# ================= CONFIG =================
TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "@Over_golsPV"

SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"

jogos_enviados = set()

def enviar_mensagem(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto}
    requests.post(url, data=payload)

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

def classificar(potencial):
    if potencial >= 3:
        return "🔥 FORTE (Over 2.5)"
    elif potencial >= 2:
        return "🟢 BOM (Over 1.5)"
    return None

def rodar_bot():
    while True:
        try:
            response = requests.get(SCOREBOARD_URL)
            data = response.json()

            for evento in data.get("events", []):
                jogo_id = evento["id"]

                casa = evento["competitions"][0]["competitors"][0]
                fora = evento["competitions"][0]["competitors"][1]

                nome_casa = casa["team"]["name"]
                nome_fora = fora["team"]["name"]

                status = evento["status"]["type"]["description"]

                print(f"DEBUG JOGO → {nome_casa} x {nome_fora} | Status: {status}")

                if "Scheduled" not in status and "Not Started" not in status:
                    continue

                if jogo_id in jogos_enviados:
                    continue

                liga = evento.get("league", {}).get("name", "")

                id_casa = casa["team"]["id"]
                id_fora = fora["team"]["id"]

                hist_casa = pegar_historico_time(id_casa)
                hist_fora = pegar_historico_time(id_fora)

                print(f"HIST → {nome_casa}: {hist_casa} | {nome_fora}: {hist_fora}")

                # 🔥 fallback para garantir funcionamento
                if not hist_casa or not hist_fora:
                    gm_casa, gs_casa = 1, 1
                    gm_fora, gs_fora = 1, 1
                else:
                    gm_casa, gs_casa = hist_casa
                    gm_fora, gs_fora = hist_fora

                potencial = (gm_casa + gs_fora) + (gm_fora + gs_casa)

                print(f"POTENCIAL → {potencial:.2f}")

                classificacao = classificar(potencial)

                if not classificacao:
                    continue

                mensagem = f"""
🚨 ENTRADA PRÉ-JOGO

{classificacao}

⚽ {nome_casa} x {nome_fora}
🏆 {liga}

🧠 Potencial: {potencial:.2f}
"""

                enviar_mensagem(mensagem)
                jogos_enviados.add(jogo_id)

        except Exception as e:
            print("Erro:", e)

        time.sleep(600)

rodar_bot()