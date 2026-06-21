"""
Gera dashboard-data.json com dados completos do ClickUp.
Chamado pelo GitHub Actions a cada 10 minutos.
"""
import json, os
from datetime import date, datetime, timedelta
import requests

TOKEN   = os.getenv("CLICKUP_TOKEN", "")
BASE    = "https://api.clickup.com/api/v2"
HEADERS = {"Authorization": TOKEN}

MEMBERS = {
    "Victor":  "101222730",
    "Gabriel": "101222731",
    "Ton":     "296568309",
}

AREAS = {
    "Marketing": ["901714663209", "901714663210", "901714663211"],
    "Vendas":    ["901714663212", "901714663213", "901714663214"],
    "Ops":       ["901714663215", "901714663216", "901714663217"],
    "Rituais":   ["901714663218", "901714663219", "901714663220", "901714663221", "901714663222"],
}
ALL_LISTS = [lid for lids in AREAS.values() for lid in lids]


def _ts(d): return int(datetime.combine(d, datetime.min.time()).timestamp() * 1000)

def _fetch(list_id):
    try:
        r = requests.get(f"{BASE}/list/{list_id}/task", headers=HEADERS,
                         params={"include_closed": "true", "limit": 200}, timeout=8)
        return r.json().get("tasks", [])
    except Exception:
        return []

def _is_closed(t):   return t["status"]["type"] == "closed"
def _is_blocked(t):  return "bloqueado" in t["status"]["status"].lower()
def _is_progress(t): return "andamento" in t["status"]["status"].lower() or "progress" in t["status"]["status"].lower()
def _has_member(t, mid): return any(a.get("id") == mid for a in t.get("assignees", []))


def gerar():
    hoje        = date.today()
    hoje_inicio = _ts(hoje)
    hoje_fim    = _ts(hoje + timedelta(days=1))
    sem_inicio  = _ts(hoje - timedelta(days=hoje.weekday()))

    # ── Busca única de todas as tarefas ──────────────────────────────────────
    todas = []
    seen  = set()
    for lid in ALL_LISTS:
        for t in _fetch(lid):
            if t["id"] not in seen:
                seen.add(t["id"])
                t["_list_area"] = next(
                    (a for a, lids in AREAS.items() if lid in lids), "Outros"
                )
                todas.append(t)

    # ── Por pessoa ────────────────────────────────────────────────────────────
    por_pessoa = {}
    bloqueadas_global = []
    total_hoje = total_conc_hoje = 0

    for nome, mid in MEMBERS.items():
        minhas = [t for t in todas if _has_member(t, mid)]

        # Hoje (filtro por due_date)
        hoje_tasks = [
            t for t in minhas
            if t.get("due_date") and hoje_inicio <= int(t["due_date"]) < hoje_fim
        ]
        conc_hoje  = [t for t in hoje_tasks if _is_closed(t)]
        pend_hoje  = [t for t in hoje_tasks if not _is_closed(t)]
        bloq_hoje  = [t for t in pend_hoje  if _is_blocked(t)]

        for t in bloq_hoje:
            dias = 0
            if t.get("date_updated"):
                dias = (datetime.now() - datetime.fromtimestamp(int(t["date_updated"]) / 1000)).days
            bloqueadas_global.append({
                "nome": t["name"],
                "responsavel": nome,
                "lista": t.get("list", {}).get("name", ""),
                "dias_bloqueado": dias,
            })

        # Semana
        cri_sem  = [t for t in minhas if t.get("date_created") and int(t["date_created"]) >= sem_inicio]
        conc_sem = [t for t in minhas if _is_closed(t) and t.get("date_updated") and int(t["date_updated"]) >= sem_inicio]

        # WIP total (todas abertas atribuídas a mim)
        wip = [t for t in minhas if not _is_closed(t)]

        por_pessoa[nome] = {
            "concluidas_hoje":   len(conc_hoje),
            "pendentes_hoje":    len(pend_hoje) - len(bloq_hoje),
            "bloqueadas_hoje":   len(bloq_hoje),
            "criadas_semana":    len(cri_sem),
            "concluidas_semana": len(conc_sem),
            "wip_total":         len(wip),
        }
        total_hoje     += len(hoje_tasks)
        total_conc_hoje += len(conc_hoje)

    # ── Saúde geral ───────────────────────────────────────────────────────────
    saude_pct    = round(total_conc_hoje / total_hoje * 100) if total_hoje > 0 else 0
    saude_status = "green" if saude_pct >= 75 else ("yellow" if saude_pct >= 40 else "red")

    # ── Distribuição de status (todas as tarefas) ─────────────────────────────
    abertas = [t for t in todas if not _is_closed(t)]
    dist = {
        "concluidas":   len([t for t in todas if _is_closed(t)]),
        "a_fazer":      len([t for t in abertas if not _is_blocked(t) and not _is_progress(t)]),
        "em_andamento": len([t for t in abertas if _is_progress(t)]),
        "bloqueadas":   len([t for t in abertas if _is_blocked(t)]),
    }

    # ── Por área ──────────────────────────────────────────────────────────────
    por_area = {}
    for area, lids in AREAS.items():
        tasks_area = [t for t in todas if t["_list_area"] == area]
        por_area[area] = {
            "total":     len(tasks_area),
            "concluidas": len([t for t in tasks_area if _is_closed(t)]),
        }

    # ── Tendência semanal (Seg → hoje) ───────────────────────────────────────
    dias_pt = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    tendencia = []
    for i in range(hoje.weekday() + 1):
        dia       = hoje - timedelta(days=hoje.weekday() - i)
        d_ini     = _ts(dia)
        d_fim     = _ts(dia + timedelta(days=1))
        criadas   = len([t for t in todas if t.get("date_created") and d_ini <= int(t["date_created"]) < d_fim])
        concluidas= len([t for t in todas if _is_closed(t) and t.get("date_updated") and d_ini <= int(t["date_updated"]) < d_fim])
        tendencia.append({"dia": dias_pt[dia.weekday()], "criadas": criadas, "concluidas": concluidas})

    # ── Alertas ───────────────────────────────────────────────────────────────
    prox7     = _ts(hoje + timedelta(days=7))
    ts_48h    = int((datetime.now() - timedelta(hours=48)).timestamp() * 1000)

    entregas_prox7   = len([t for t in todas if not _is_closed(t) and t.get("due_date") and hoje_inicio <= int(t["due_date"]) < prox7])
    parados_48h      = len([t for t in todas if not _is_closed(t) and t.get("date_updated") and int(t["date_updated"]) < ts_48h])
    bloq_2d          = len([b for b in bloqueadas_global if b["dias_bloqueado"] >= 2])
    wip_medio        = round(sum(p["wip_total"] for p in por_pessoa.values()) / max(len(por_pessoa), 1), 1)

    alertas = {
        "entregas_7_dias":          entregas_prox7,
        "projetos_sem_atualizacao": parados_48h,
        "bloqueadas_2_dias":        bloq_2d,
        "wip_medio":                wip_medio,
        "clientes_sem_contato":     0,
    }

    data = {
        "atualizado_em":    datetime.now().strftime("%d/%m/%Y %H:%M"),
        "saude_geral":      {"pct": saude_pct, "status": saude_status},
        "por_pessoa":       por_pessoa,
        "bloqueadas":       bloqueadas_global,
        "por_area":         por_area,
        "distribuicao":     dist,
        "tendencia_semanal": tendencia,
        "alertas":          alertas,
    }

    with open("dashboard-data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"OK — saúde {saude_pct}% | dist: {dist} | alertas: {alertas}")


if __name__ == "__main__":
    gerar()
