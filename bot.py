import requests
import time
import random
from datetime import datetime, timedelta

# ================= CONFIG =================
TOKEN = "8686967499:AAGDgl9xyuvstuZj1n_cuUlSeQGtZKd4N8M"
CHAT_ID = "@Over_golsPV"

URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"

# ================= LIGAS BOAS =================
ligas_boas = [
    "england", "premier",
    "spain", "laliga",
    "italy", "serie a",
    "germany", "bundesliga",
    "france", "ligue",
    "brazil", "brasileirão",
    "argentina",
    "champions",
    "europa",
    "conference",
    "libertadores",
    "sudamericana"
]

def liga_valida(nome):
    nome = nome.lower()
    return any(l in nome for l in ligas_boas)

# ================= TELEGRAM =================
def enviar(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except:
        print("Erro ao enviar mensagem")

# ================= LINK BET365 =================
def gerar_link(jogo):
    busca = jogo.replace(" ", "+").replace("x", "vs")
    return f"https://www.bet365.com/#/AX/K^{busca}"

# ================= HISTÓRICO =================
def historico(team_id):
    try:
        data = requests.get(
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/teams/{team_id}/schedule"
        ).json()

        jogos = data.get("events", [])[:10]

        gm, gs, total = 0, 0, 0

        for j in jogos:
            try:
                comps = j["competitions"][0]["competitors"]

                if "score" not in comps[0] or "score" not in comps[1]:
                    continue

                if comps[0]["score"] is None or comps[1]["score"] is None:
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

# ================= LOOP =================
def rodar():
    while True:
        try:
            data = requests.get(URL).json()
            candidatos = []

            for e in data.get("events", []):

                status = e["status"]["type"]["description"]

                if "Scheduled" not in status and "Not Started" not in status:
                    continue

                # 🔥 FILTRO DE LIGA
                liga = e.get("league", {}).get("name", "")
                if not liga_valida(liga):
                    continue

                casa = e["competitions"][0]["competitors"][0]
                fora = e["competitions"][0]["competitors"][1]

                nome_casa = casa["team"]["name"]
                nome_fora = fora["team"]["name"]

                hist_c = historico(casa["team"]["id"])
                hist_f = historico(fora["team"]["id"])

                usando_fallback = False

                if not hist_c or not hist_f:
                    usando_fallback = True
                    gm_c = random.uniform(1.2, 1.7)
                    gs_c = random.uniform(1.0, 1.6)
                    gm_f = random.uniform(1.2, 1.7)
                    gs_f = random.uniform(1.0, 1.6)
                else:
                    gm_c, gs_c = hist_c
                    gm_f, gs_f = hist_f

                # 🔥 FILTROS DE QUALIDADE
                if gm_c < 1.3 or gm_f < 1.3:
                    continue

                if gs_c < 0.9 and gs_f < 0.9:
                    continue

                potencial = ((gm_c + gs_f) / 2) + ((gm_f + gs_c) / 2)
                prob = min(int((potencial / 3.5) * 100), 95)

                if usando_fallback:
                    prob = max(prob - 10, 60)

                if prob < 70:
                    continue

                nivel = "ELITE" if prob >= 80 else "FORTE"

                mercado = "Over 2.5" if potencial >= 3.0 else "Over 1.5"

                hora_utc = datetime.fromisoformat(e["date"].replace("Z", ""))
                hora_br = hora_utc - timedelta(hours=3)

                candidatos.append({
                    "jogo": f"{nome_casa} x {nome_fora}",
                    "prob": prob,
                    "nivel": nivel,
                    "mercado": mercado,
                    "hora": hora_br.strftime("%H:%M"),
                    "link": gerar_link(f"{nome_casa} vs {nome_fora}")
                })

            candidatos = sorted(candidatos, key=lambda x: x["prob"], reverse=True)

            elites = [c for c in candidatos if c["nivel"] == "ELITE"]
            fortes = [c for c in candidatos if c["nivel"] == "FORTE"]

            # ================= DUPLA =================
            dupla = (elites + fortes)[:2]

            if len(dupla) == 2:
                odd = 1
                texto = ""
                links = ""

                for j in dupla:
                    odd *= 1.30 if "1.5" in j["mercado"] else 1.80
                    texto += f"\n• {j['jogo']} → {j['mercado']}"
                    links += f"\n{j['link']}"

                enviar(f"""
🛡️ DUPLA DO DIA

{texto}

💰 Odd estimada: {odd:.2f}

🎯 COMO APOSTAR:
1. Acesse os jogos abaixo
2. Selecione o mercado indicado
3. Monte o bilhete

🔗 Jogos:
{links}

💰 Stake: 1-2%
""")

            # ================= TRIPLA =================
            tripla = (elites[:1] + fortes[:2])[:3]

            if len(tripla) == 3:
                odd = 1
                texto = ""
                links = ""

                for j in tripla:
                    odd *= 1.30 if "1.5" in j["mercado"] else 1.80
                    texto += f"\n• {j['jogo']} → {j['mercado']}"
                    links += f"\n{j['link']}"

                enviar(f"""
🔥 TRIPLA DO DIA

{texto}

💰 Odd estimada: {odd:.2f}

🎯 COMO APOSTAR:
1. Acesse os jogos abaixo
2. Selecione o mercado indicado
3. Monte o bilhete

🔗 Jogos:
{links}

💰 Stake: 0.5-1%
""")

            print(f"Jogos filtrados: {len(candidatos)}")

        except Exception as e:
            print("Erro:", e)

        time.sleep(1800)

rodar()