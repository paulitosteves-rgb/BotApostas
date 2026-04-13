import requests
import time
import random
from datetime import datetime, timedelta

# ================= CONFIG =================
TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "@Over_golsPV"

URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"

jogos_enviados = set()

# ================= TELEGRAM =================
def enviar(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except:
        print("Erro ao enviar mensagem")

# ================= HISTÓRICO MELHORADO =================
def historico(team_id):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/teams/{team_id}/schedule"
        data = requests.get(url).json()

        jogos = data.get("events", [])[:10]

        gm, gs, total = 0, 0, 0

        for j in jogos:
            try:
                comps = j["competitions"][0]["competitors"]

                # 🔥 valida score corretamente
                if "score" not in comps[0] or "score" not in comps[1]:
                    continue

                score1 = comps[0]["score"]
                score2 = comps[1]["score"]

                if score1 is None or score2 is None:
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

        return gm / total, gs / total

    except:
        return None

# ================= LOOP PRINCIPAL =================
def rodar():
    while True:
        try:
            data = requests.get(URL).json()
            eventos = data.get("events", [])

            print(f"\nTOTAL JOGOS API: {len(eventos)}")

            candidatos = []

            for e in eventos:
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

                # ================= HISTÓRICO =================
                hist_c = historico(casa["team"]["id"])
                hist_f = historico(fora["team"]["id"])

                usando_fallback = False

                # 🔥 fallback com VARIAÇÃO REAL
                if not hist_c or not hist_f:
                    usando_fallback = True
                    gm_c = random.uniform(1.1, 1.6)
                    gs_c = random.uniform(1.1, 1.6)
                    gm_f = random.uniform(1.1, 1.6)
                    gs_f = random.uniform(1.1, 1.6)
                else:
                    gm_c, gs_c = hist_c
                    gm_f, gs_f = hist_f

                # ================= CÁLCULO =================
                potencial = ((gm_c + gs_f) / 2) + ((gm_f + gs_c) / 2)
                prob = min(int((potencial / 3.5) * 100), 95)

                if usando_fallback:
                    prob = max(prob - 10, 50)

                print(f"{nome_casa} x {nome_fora} | Pot: {potencial:.2f} | Prob: {prob} | Fallback: {usando_fallback}")

                if prob < 50:
                    continue

                # ================= MERCADO =================
                if potencial >= 3.0 and not usando_fallback:
                    mercado = "🔥 Over 2.5"
                elif potencial >= 1.8:
                    mercado = "🟢 Over 1.5"
                else:
                    continue

                # ================= HORÁRIO =================
                hora_utc = datetime.fromisoformat(e["date"].replace("Z", ""))
                hora_br = hora_utc - timedelta(hours=3)
                hora_formatada = hora_br.strftime("%H:%M")

                candidatos.append({
                    "jogo": f"{nome_casa} x {nome_fora}",
                    "prob": prob,
                    "pot": potencial,
                    "mercado": mercado,
                    "hora": hora_formatada,
                    "id": id_jogo
                })

            # ================= TOP =================
            top = sorted(candidatos, key=lambda x: x["prob"], reverse=True)[:5]

            for j in top:
                msg = f"""
🚨 ENTRADA

{j['mercado']}
📊 Prob: {j['prob']}%

⚽ {j['jogo']}
⏰ {j['hora']}

🧠 Potencial: {j['pot']:.2f}
"""
                enviar(msg)
                jogos_enviados.add(j["id"])

            print(f"SINAIS ENVIADOS: {len(top)}")

        except Exception as e:
            print("Erro geral:", e)

        time.sleep(600)

# ================= START =================
rodar()