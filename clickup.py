import requests
from datetime import datetime, date
from config import CLICKUP_TOKEN, LIST_IDS

BASE = "https://api.clickup.com/api/v2"
HEADERS = {"Authorization": CLICKUP_TOKEN, "Content-Type": "application/json"}


def _get(path, params=None):
    r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()


def _post(path, data):
    r = requests.post(f"{BASE}{path}", headers=HEADERS, json=data)
    r.raise_for_status()
    return r.json()


def get_tasks_hoje(member_clickup_id: str) -> dict:
    """Retorna tarefas do membro divididas por status para hoje."""
    hoje_ts = int(datetime.combine(date.today(), datetime.min.time()).timestamp() * 1000)
    amanha_ts = hoje_ts + 86400000

    params = {
        "assignees[]": member_clickup_id,
        "due_date_gt": hoje_ts - 1,
        "due_date_lt": amanha_ts,
        "include_closed": "true",
    }

    todas = []
    for list_id in LIST_IDS.values():
        try:
            resp = _get(f"/list/{list_id}/task", params)
            todas.extend(resp.get("tasks", []))
        except Exception:
            pass

    concluidas = [t for t in todas if t["status"]["status"].lower() in ["concluido", "concluído", "done", "complete"]]
    pendentes  = [t for t in todas if t["status"]["status"].lower() not in ["concluido", "concluído", "done", "complete"]]
    bloqueadas = [t for t in pendentes if t["status"]["status"].lower() == "bloqueado"]
    em_andamento = [t for t in pendentes if t["status"]["status"].lower() == "em andamento"]
    a_fazer    = [t for t in pendentes if t["status"]["status"].lower() == "a fazer"]

    return {
        "concluidas":    concluidas,
        "em_andamento":  em_andamento,
        "bloqueadas":    bloqueadas,
        "a_fazer":       a_fazer,
        "todas_pendentes": pendentes,
    }


def get_todas_tarefas_membro(member_clickup_id: str) -> list:
    """Retorna todas as tarefas abertas do membro (sem filtro de data)."""
    params = {
        "assignees[]": member_clickup_id,
        "include_closed": "false",
    }

    todas = []
    for list_id in LIST_IDS.values():
        try:
            resp = _get(f"/list/{list_id}/task", params)
            todas.extend(resp.get("tasks", []))
        except Exception:
            pass

    return todas


def criar_relatorio_daily(nome: str, concluidas: list, nao_concluidas: list, resposta_wpp: str) -> dict:
    """Cria tarefa de relatório da Daily Sync no ClickUp."""
    hoje = date.today().strftime("%d/%m/%Y")

    linhas_feitas = "\n".join([f"  ✓ {t['name']}" for t in concluidas]) or "  Nenhuma"
    linhas_nao_feitas = "\n".join([f"  ✗ {t['name']}" for t in nao_concluidas]) or "  Nenhuma"

    descricao = f"""Daily — {nome} — {hoje}

O QUE FEZ HOJE:
{linhas_feitas}

O QUE NÃO CONCLUIU:
{linhas_nao_feitas}

MOTIVO / BLOQUEIO E PLANO DE AMANHÃ:
  {resposta_wpp}
"""

    task = _post(f"/list/{LIST_IDS['daily_sync']}/task", {
        "name": f"Daily {nome} — {hoje}",
        "description": descricao,
        "status": "Concluido",
    })

    return task


def criar_tarefa(list_id: str, nome: str, descricao: str, assignee_id: str, due_date: int = None) -> dict:
    """Cria uma nova tarefa em qualquer lista."""
    data = {
        "name": nome,
        "description": descricao,
        "assignees": [int(assignee_id)],
        "status": "A Fazer",
    }
    if due_date:
        data["due_date"] = due_date

    return _post(f"/list/{list_id}/task", data)


def atualizar_status_tarefa(task_id: str, status: str) -> dict:
    r = requests.put(
        f"{BASE}/task/{task_id}",
        headers=HEADERS,
        json={"status": status}
    )
    r.raise_for_status()
    return r.json()
