"""
Gera dashboard-data.json com dados do ClickUp.
Chamado pelo GitHub Actions a cada 10 minutos.
"""
import json
import os
from datetime import date, datetime, timedelta
import requests

TOKEN = os.getenv("CLICKUP_TOKEN", "")
BASE = "https://api.clickup.com/api/v2"
HEADERS = {"Authorization": TOKEN}

MEMBERS = {
    "Victor":  "101222730",
    "Gabriel": "101222731",
    "Ton":     "296568309",
}

AREAS = {
    "Marketing":  ["901714663209", "901714663210", "901714663211"],
    "Vendas":     ["901714663212", "901714663213", "901714663214"],
    "Ops":        ["901714663215", "901714663216", "901714663217"],
    "Rituais":    ["901714663218", "901714663219", "901714663220", "901714663221", "901714663222"],
}


def _get_tasks(list_id, params=None):
    try:
        r = requests.get(f"{BASE}/list/{list_id}/task", headers=HEADERS, params=params or {}, timeout=8)
        return r.json().get("tasks", [])
    except Exception:
        return []


def _hoje_range():
    hoje = datetime.combine(date.today(), datetime.min.time())
    return int(hoje.timestamp() * 1000), int((hoje + timedelta(days=1)).timestamp() * 1000)


def _semana_range():
    hoje = date.today()
    inicio = hoje - timedelta(days=hoje.weekday())
    ts_inicio = int(datetime.combine(inicio, datetime.min.time()).timestamp() * 1000)
    ts_fim = int(datetime.combine(hoje + timedelta(days=1), datetime.min.time()).timestamp() * 1000)
    return ts_inicio, ts_fim


def gerar():
    hoje_inicio, hoje_fim = _hoje_range()
    semana_inicio, semana_fim = _semana_range()

    por_pessoa = {}
    total_hoje = 0
    total_concluidas_hoje = 0
    bloqueadas_global = []

    for nome, member_id in MEMBERS.items():
        tarefas_hoje = []
        for list_ids in AREAS.values():
            for lid in list_ids:
                tasks = _get_tasks(lid, {
                    "assignees[]": member_id,
                    "due_date_gt": hoje_inicio - 1,
                    "due_date_lt": hoje_fim,
                    "include_closed": "true",
                })
                tarefas_hoje.extend(tasks)

        concluidas   = [t for t in tarefas_hoje if t["status"]["type"] == "closed"]
        pendentes    = [t for t in tarefas_hoje if t["status"]["type"] != "closed"]
        bloqueadas   = [t for t in pendentes if "bloqueado" in t["status"]["status"].lower()]

        for t in bloqueadas:
            bloqueadas_global.append({
                "nome": t["name"],
                "responsavel": nome,
                "lista": t.get("list", {}).get("name", ""),
            })

        tarefas_semana = []
        for list_ids in AREAS.values():
            for lid in list_ids:
                tasks = _get_tasks(lid, {
                    "assignees[]": member_id,
                    "date_created_gt": semana_inicio,
                    "date_created_lt": semana_fim,
                    "include_closed": "true",
                })
                tarefas_semana.extend(tasks)

        por_pessoa[nome] = {
            "concluidas_hoje":   len(concluidas),
            "pendentes_hoje":    len(pendentes) - len(bloqueadas),
            "bloqueadas_hoje":   len(bloqueadas),
            "criadas_semana":    len(tarefas_semana),
            "concluidas_semana": len([t for t in tarefas_semana if t["status"]["type"] == "closed"]),
        }

        total_hoje += len(tarefas_hoje)
        total_concluidas_hoje += len(concluidas)

    saude_pct = round((total_concluidas_hoje / total_hoje * 100) if total_hoje > 0 else 0)
    saude_status = "green" if saude_pct >= 75 else ("yellow" if saude_pct >= 40 else "red")

    por_area = {}
    for area_nome, list_ids in AREAS.items():
        total = conc = 0
        for lid in list_ids:
            tasks = _get_tasks(lid, {"include_closed": "true"})
            total += len(tasks)
            conc  += len([t for t in tasks if t["status"]["type"] == "closed"])
        por_area[area_nome] = {"total": total, "concluidas": conc}

    data = {
        "atualizado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "saude_geral":   {"pct": saude_pct, "status": saude_status},
        "por_pessoa":    por_pessoa,
        "bloqueadas":    bloqueadas_global,
        "por_area":      por_area,
    }

    with open("dashboard-data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Dashboard gerado: saúde {saude_pct}% | {total_concluidas_hoje}/{total_hoje} tarefas hoje")


if __name__ == "__main__":
    gerar()
