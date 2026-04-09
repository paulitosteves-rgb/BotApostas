import requests
import time
from datetime import datetime, timedelta

# ================= CONFIG =================
TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "@Over_golsPV"

URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"

jogos_enviados = set()

# ================= TELEGRAM =================
def enviar(msg):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={
        "chat_id": CHAT_ID,
        "text": msg
    })

# ================= HISTÓRICO =================
def historico(team_id):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/teams/{team_id}/schedule"
        data = requests.get(url).json()

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

# ================= LOOP =================
def rodar():
    while True:
        try:
            data = requests.get(URL).json()

            candidatos = []

            for e in data.get("events", []):
                id_jogo = e["id"]

                if id_jogo in jogos_enviados:
                    continue

                status = e["status"]["type"]["description"]

                if "Scheduled" not in status and "Not Started" not in status:
                    continue

                casa = e["competitions"][0]["competitors"][0]
                fora = e["competitions"][0]["competitors"][1]

                nome_casa = casa["team"]["name"]
                nome_fora = fora["team"]["name"]

                id_casa = casa["team"]["id"]
                id_fora = fora["team"]["id"]

                hist_c = historico(id_casa)
                hist_f = historico(id_fora)

                if not hist_c or not hist_f:
                    continue  # 🔥 agora ignoramos lixo

                gm_c, gs_c = hist_c
                gm_f, gs_f = hist_f

                # 🔥 cálculo refinado
                ataque = (gm_c + gm_f) / 2
                defesa = (gs_c + gs_f) / 2

                potencial = (gm_c + gs_f) + (gm_f + gs_c)

                prob = min(int((potencial / 4) * 100), 95)

                if prob < 60 or potencial < 2.2:
                    continue

                odd_justa = round(100 / prob, 2)

                # 🔥 EV+ simples (simulação mercado)
                odd_minima = 1.30 if potencial >= 3 else 1.20

                if odd_justa > odd_minima:
                    continue  # sem valor

                mercado = "Over 2.5" if potencial >= 3.2 else "Over 1.5"

                candidatos.append({
                    "jogo": f"{nome_casa} x {nome_fora}",
                    "liga": e.get("league", {}).get("name", ""),
                    "prob": prob,
                    "pot": potencial,
                    "mercado": mercado
                })

            # ================= TOP 5 =================
            top = sorted(candidatos, key=lambda x: x["prob"], reverse=True)[:5]

            for j in top:
                msg = f"""
🚨 TOP ENTRADA

🔥 {j['mercado']}
📊 Prob: {j['prob']}%

⚽ {j['jogo']}
🏆 {j['liga']}

🧠 Potencial: {j['pot']:.2f}
"""
                enviar(msg)
                jogos_enviados.add(j["jogo"])

            # ================= MÚLTIPLA =================
            if len(top) >= 3:
                odd_total = 1

                texto = "🔥 MÚLTIPLA DO DIA\n\n"

                for j in top[:3]:
                    odd_est = 1.25 if j["mercado"] == "Over 1.5" else 1.50
                    odd_total *= odd_est

                    texto += f"{j['jogo']} — {j['mercado']}\n"

                texto += f"\n💰 Odd estimada: {odd_total:.2f}"

                enviar(texto)

            print(f"Loop OK - {len(top)} sinais")

        except Exception as e:
            print("Erro:", e)

        time.sleep(600)

rodar()