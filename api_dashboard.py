"""
Endpoint que agrega dados do ClickUp e serve para o dashboard.
"""
from datetime import date, datetime, timedelta
from fastapi import APIRouter
from config import MEMBERS, LIST_IDS, CLICKUP_TOKEN
import requests

router = APIRouter(prefix="/api")
BASE = "https://api.clickup.com/api/v2"
HEADERS = {"Authorization": CLICKUP_TOKEN}

AREAS = {
    "Marketing":  ["901714663209", "901714663210", "901714663211"],
    "Vendas":     ["901714663212", "901714663213", "901714663214"],
    "Ops":        ["901714663215", "901714663216", "901714663217"],
    "Rituais":    ["901714663218", "901714663219", "901714663220", "901714663221", "901714663222"],
}


def _get_tasks_list(list_id: str, params: dict = None) -> list:
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
    inicio = hoje - timedelta(days=hoje.weekday())  # segunda-feira
    ts_inicio = int(datetime.combine(inicio, datetime.min.time()).timestamp() * 1000)
    ts_fim = int(datetime.combine(hoje + timedelta(days=1), datetime.min.time()).timestamp() * 1000)
    return ts_inicio, ts_fim


@router.get("/dashboard")
def get_dashboard():
    hoje_inicio, hoje_fim = _hoje_range()
    semana_inicio, semana_fim = _semana_range()

    # ── Por pessoa ──────────────────────────────────────────────────────────
    por_pessoa = {}
    total_hoje = 0
    total_concluidas_hoje = 0
    bloqueadas_global = []

    for nome, dados in MEMBERS.items():
        member_id = dados["clickup_id"]
        tarefas_hoje = []

        for list_ids in AREAS.values():
            for lid in list_ids:
                tasks = _get_tasks_list(lid, {
                    "assignees[]": member_id,
                    "due_date_gt": hoje_inicio - 1,
                    "due_date_lt": hoje_fim,
                    "include_closed": "true",
                })
                tarefas_hoje.extend(tasks)

        concluidas = [t for t in tarefas_hoje if "conclu" in t["status"]["status"].lower() or t["status"]["type"] == "closed"]
        pendentes  = [t for t in tarefas_hoje if t not in concluidas]
        bloqueadas = [t for t in pendentes if "bloqueado" in t["status"]["status"].lower()]

        for t in bloqueadas:
            bloqueadas_global.append({
                "nome": t["name"],
                "responsavel": nome,
                "lista": t.get("list", {}).get("name", ""),
            })

        # Semana
        tarefas_semana = []
        for list_ids in AREAS.values():
            for lid in list_ids:
                tasks = _get_tasks_list(lid, {
                    "assignees[]": member_id,
                    "date_created_gt": semana_inicio,
                    "date_created_lt": semana_fim,
                    "include_closed": "true",
                })
                tarefas_semana.extend(tasks)

        criadas_semana    = len(tarefas_semana)
        concluidas_semana = len([t for t in tarefas_semana if "conclu" in t["status"]["status"].lower() or t["status"]["type"] == "closed"])

        por_pessoa[nome] = {
            "concluidas_hoje":    len(concluidas),
            "pendentes_hoje":     len(pendentes) - len(bloqueadas),
            "bloqueadas_hoje":    len(bloqueadas),
            "criadas_semana":     criadas_semana,
            "concluidas_semana":  concluidas_semana,
        }

        total_hoje += len(tarefas_hoje)
        total_concluidas_hoje += len(concluidas)

    # ── Saúde geral ─────────────────────────────────────────────────────────
    saude_pct = round((total_concluidas_hoje / total_hoje * 100) if total_hoje > 0 else 0)
    if saude_pct >= 75:
        saude_status = "green"
    elif saude_pct >= 40:
        saude_status = "yellow"
    else:
        saude_status = "red"

    # ── Por área ────────────────────────────────────────────────────────────
    por_area = {}
    for area_nome, list_ids in AREAS.items():
        total = 0
        concluidas = 0
        for lid in list_ids:
            tasks = _get_tasks_list(lid, {"include_closed": "true"})
            total += len(tasks)
            concluidas += len([t for t in tasks if "conclu" in t["status"]["status"].lower() or t["status"]["type"] == "closed"])
        por_area[area_nome] = {"total": total, "concluidas": concluidas}

    return {
        "atualizado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "saude_geral": {"pct": saude_pct, "status": saude_status},
        "por_pessoa": por_pessoa,
        "bloqueadas": bloqueadas_global,
        "por_area": por_area,
    }
