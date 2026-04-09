import requests
import time
from datetime import datetime, timedelta

# ================= CONFIG =================
TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "@Over_golsPV"

URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"

jogos_enviados = set()

def enviar(msg):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={
        "chat_id": CHAT_ID,
        "text": msg
    })

def historico(team_id):
    try:
        data = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/teams/{team_id}/schedule").json()
        jogos = data.get("events", [])[:10]

        gm, gs, total = 0, 0, 0

        for j in jogos:
            try:
                comps = j["competitions"][0]["competitors"]

                if not comps[0].get("score") or not comps[1].get("score"):
                    continue

                for t in comps:
                    if t["team"]["id"] == team_id:
                        gm += int(t["score"])
                    else:
                        gs += int(t["score"])

                total += 1
            except:
                continue

        if total == 0:
            return None

        return gm/total, gs/total

    except:
        return None

def rodar():
    while True:
        try:
            data = requests.get(URL).json()
            candidatos = []

            for e in data.get("events", []):
                status = e["status"]["type"]["description"]

                if "Scheduled" not in status and "Not Started" not in status:
                    continue

                casa = e["competitions"][0]["competitors"][0]
                fora = e["competitions"][0]["competitors"][1]

                nome_casa = casa["team"]["name"]
                nome_fora = fora["team"]["name"]

                id_jogo = e["id"]

                if id_jogo in jogos_enviados:
                    continue

                hist_c = historico(casa["team"]["id"])
                hist_f = historico(fora["team"]["id"])

                if not hist_c or not hist_f:
                    continue

                gm_c, gs_c = hist_c
                gm_f, gs_f = hist_f

                potencial = (gm_c + gs_f) + (gm_f + gs_c)
                prob = min(int((potencial / 4) * 100), 95)

                if prob < 60:
                    continue

                # 🔥 NOVA REGRA
                if potencial >= 3.6:
                    mercado = "🔥 Over 2.5"
                elif potencial >= 2.4:
                    mercado = "🟢 Over 1.5"
                else:
                    continue

                # ⏰ horário
                hora = datetime.fromisoformat(e["date"].replace("Z", ""))
                hora_formatada = hora.strftime("%H:%M")

                candidatos.append({
                    "jogo": f"{nome_casa} x {nome_fora}",
                    "liga": e.get("league", {}).get("name", ""),
                    "prob": prob,
                    "pot": potencial,
                    "mercado": mercado,
                    "hora": hora_formatada,
                    "id": id_jogo
                })

            # 🔥 LIMITA TOP 5
            top = sorted(candidatos, key=lambda x: x["prob"], reverse=True)[:5]

            for j in top:
                msg = f"""
🚨 TOP ENTRADA

{j['mercado']}
📊 Prob: {j['prob']}%

⚽ {j['jogo']}
🏆 {j['liga']}
⏰ {j['hora']}

🧠 Potencial: {j['pot']:.2f}
"""
                enviar(msg)
                jogos_enviados.add(j["id"])

            print(f"Loop OK - {len(top)} sinais enviados")

        except Exception as e:
            print("Erro:", e)

        time.sleep(600)

rodar()