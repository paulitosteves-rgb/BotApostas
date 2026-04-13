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

# ================= MÚLTIPLAS =================
def gerar_multiplas(candidatos):
    fortes = [c for c in candidatos if c["prob"] >= 70]

    if len(fortes) < 2:
        return []

    fortes = sorted(fortes, key=lambda x: x["prob"], reverse=True)

    multiplas = []

    # SEGURA (2 jogos)
    jogos_segura = fortes[:2]
    odd_total = 1
    desc = ""

    for j in jogos_segura:
        odd = 1.30 if "1.5" in j["mercado"] else 1.80
        odd_total *= odd
        desc += f"\n• {j['jogo']} ({j['mercado']})"

    multiplas.append({
        "tipo": "🛡️ MÚLTIPLA SEGURA",
        "jogos": desc,
        "odd": odd_total
    })

    # AGRESSIVA (3 jogos)
    if len(fortes) >= 3:
        jogos_agressiva = fortes[:3]
        odd_total = 1
        desc = ""

        for j in jogos_agressiva:
            odd = 1.30 if "1.5" in j["mercado"] else 1.80
            odd_total *= odd
            desc += f"\n• {j['jogo']} ({j['mercado']})"

        multiplas.append({
            "tipo": "🔥 MÚLTIPLA AGRESSIVA",
            "jogos": desc,
            "odd": odd_total
        })

    return multiplas

# ================= LOOP =================
def rodar():
    while True:
        try:
            data = requests.get(URL).json()
            eventos = data.get("events", [])

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

                hist_c = historico(casa["team"]["id"])
                hist_f = historico(fora["team"]["id"])

                usando_fallback = False

                if not hist_c or not hist_f:
                    usando_fallback = True
                    gm_c = random.uniform(1.1, 1.6)
                    gs_c = random.uniform(1.1, 1.6)
                    gm_f = random.uniform(1.1, 1.6)
                    gs_f = random.uniform(1.1, 1.6)
                else:
                    gm_c, gs_c = hist_c
                    gm_f, gs_f = hist_f

                # 🔥 FILTROS DE QUALIDADE
                if gm_c < 1.2 and gm_f < 1.2:
                    continue

                if gs_c < 0.8 and gs_f < 0.8:
                    continue

                # 🔥 CÁLCULO
                potencial = ((gm_c + gs_f) / 2) + ((gm_f + gs_c) / 2)
                prob = min(int((potencial / 3.5) * 100), 95)

                if usando_fallback:
                    prob = max(prob - 10, 50)

                if prob < 65:
                    continue

                # 🔥 NÍVEL
                if prob >= 80:
                    nivel = "💎 ELITE"
                elif prob >= 70:
                    nivel = "🔥 FORTE"
                else:
                    nivel = "⚠️ MODERADO"

                # 🔥 MERCADO
                if potencial >= 3.0 and not usando_fallback:
                    mercado = "🔥 Over 2.5"
                elif potencial >= 1.8:
                    mercado = "🟢 Over 1.5"
                else:
                    continue

                # 🔥 HORÁRIO
                hora_utc = datetime.fromisoformat(e["date"].replace("Z", ""))
                hora_br = hora_utc - timedelta(hours=3)
                hora_formatada = hora_br.strftime("%H:%M")

                candidatos.append({
                    "jogo": f"{nome_casa} x {nome_fora}",
                    "prob": prob,
                    "pot": potencial,
                    "mercado": mercado,
                    "hora": hora_formatada,
                    "nivel": nivel,
                    "id": id_jogo,
                    "gm_c": gm_c,
                    "gm_f": gm_f,
                    "gs_c": gs_c,
                    "gs_f": gs_f
                })

            # ================= ORGANIZAÇÃO =================
            elites = [c for c in candidatos if c["prob"] >= 80]
            fortes = [c for c in candidatos if 70 <= c["prob"] < 80]
            moderados = [c for c in candidatos if c["prob"] < 70]

            top = sorted(elites, key=lambda x: x["prob"], reverse=True)[:3]
            top += sorted(fortes, key=lambda x: x["prob"], reverse=True)[:2]

            if len(top) < 3:
                top += sorted(moderados, key=lambda x: x["prob"], reverse=True)[:2]

            # ================= ENVIO SINAIS =================
            for j in top:
                msg = f"""
🚨 ENTRADA {j['nivel']}

{j['mercado']}
📊 Prob: {j['prob']}%

⚽ {j['jogo']}
⏰ {j['hora']}

📈 Ataque: {j['gm_c']:.1f} x {j['gm_f']:.1f}
🧱 Defesa: {j['gs_c']:.1f} x {j['gs_f']:.1f}

🧠 Potencial: {j['pot']:.2f}
💰 Stake sugerida: 1-2%
"""
                enviar(msg)
                jogos_enviados.add(j["id"])

            # ================= ENVIO MÚLTIPLAS =================
            multiplas = gerar_multiplas(candidatos)

            for m in multiplas:
                msg = f"""
{m['tipo']}

{m['jogos']}

💰 Odd estimada: {m['odd']:.2f}
⚠️ Gestão: 0.5% a 1% da banca
"""
                enviar(msg)

            print(f"SINAIS PREMIUM: {len(top)} | MULTIPLAS: {len(multiplas)}")

        except Exception as e:
            print("Erro geral:", e)

        time.sleep(600)

# ================= START =================
rodar()