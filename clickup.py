import requests
from datetime import datetime, date
from config import CLICKUP_TOKEN, LIST_IDS, SOCIOS_LIST_IDS

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


def get_tasks_socios(lista_id: str) -> dict:
    """Retorna tarefas da lista pessoal do sócio em Gestão Sócios."""
    try:
        resp = _get(f"/list/{lista_id}/task", {"include_closed": "false"})
        todas = resp.get("tasks", [])
    except Exception:
        todas = []

    def s(t):
        return t["status"]["status"].lower()

    concluidas   = [t for t in todas if s(t) in ("concluido", "concluído", "complete", "done")]
    pendentes    = [t for t in todas if s(t) not in ("concluido", "concluído", "complete", "done")]
    bloqueadas   = [t for t in pendentes if s(t) == "bloqueado"]
    em_andamento = [t for t in pendentes if s(t) == "em andamento"]
    planning     = [t for t in pendentes if s(t) == "planning"]
    backlog      = [t for t in pendentes if s(t) == "backlog"]

    return {
        "concluidas":      concluidas,
        "em_andamento":    em_andamento,
        "planning":        planning,
        "backlog":         backlog,
        "bloqueadas":      bloqueadas,
        "todas_pendentes": pendentes,
    }


def criar_tarefa_socios(lista_id: str, nome: str, assignee_id: str) -> dict:
    """Cria tarefa na lista pessoal do sócio com status BACKLOG."""
    return _post(f"/list/{lista_id}/task", {
        "name": nome,
        "assignees": [int(assignee_id)] if assignee_id else [],
        "status": "backlog",
    })


def criar_multiplas_tarefas(lista_id: str, tarefas: list, assignee_id: str) -> list:
    """Cria várias tarefas de uma vez. tarefas = [{nome, prazo}]"""
    criadas = []
    for t in tarefas:
        try:
            r = _post(f"/list/{lista_id}/task", {
                "name": t.get("nome", t.get("name", "")),
                "assignees": [int(assignee_id)] if assignee_id else [],
                "status": "planning",
            })
            criadas.append(r)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erro ao criar tarefa '{t}': {e}")
    return criadas


def get_tasks_hoje(member_clickup_id: str) -> dict:
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

    concluidas   = [t for t in todas if t["status"]["status"].lower() in ("concluido", "concluído", "done", "complete")]
    pendentes    = [t for t in todas if t["status"]["status"].lower() not in ("concluido", "concluído", "done", "complete")]
    bloqueadas   = [t for t in pendentes if t["status"]["status"].lower() == "bloqueado"]
    em_andamento = [t for t in pendentes if t["status"]["status"].lower() == "em andamento"]
    a_fazer      = [t for t in pendentes if t["status"]["status"].lower() == "a fazer"]

    return {
        "concluidas":      concluidas,
        "em_andamento":    em_andamento,
        "bloqueadas":      bloqueadas,
        "a_fazer":         a_fazer,
        "todas_pendentes": pendentes,
    }


def get_todas_tarefas_membro(member_clickup_id: str) -> list:
    params = {"assignees[]": member_clickup_id, "include_closed": "false"}
    todas = []
    for list_id in LIST_IDS.values():
        try:
            resp = _get(f"/list/{list_id}/task", params)
            todas.extend(resp.get("tasks", []))
        except Exception:
            pass
    return todas


def criar_relatorio_daily(nome: str, concluidas: list, nao_concluidas: list, resposta_wpp: str) -> dict:
    hoje = date.today().strftime("%d/%m/%Y")
    linhas_feitas    = "\n".join([f"  ✓ {t['name']}" for t in concluidas]) or "  Nenhuma"
    linhas_nao_feitas = "\n".join([f"  ✗ {t['name']}" for t in nao_concluidas]) or "  Nenhuma"
    descricao = (
        f"Daily — {nome} — {hoje}\n\n"
        f"O QUE FEZ HOJE:\n{linhas_feitas}\n\n"
        f"O QUE NÃO CONCLUIU:\n{linhas_nao_feitas}\n\n"
        f"MOTIVO / BLOQUEIO E PLANO DE AMANHÃ:\n  {resposta_wpp}\n"
    )
    return _post(f"/list/{LIST_IDS['daily_sync']}/task", {
        "name": f"Daily {nome} — {hoje}",
        "description": descricao,
        "status": "Concluido",
    })


def criar_tarefa(list_id: str, nome: str, descricao: str, assignee_id: str, due_date: int = None) -> dict:
    data = {"name": nome, "description": descricao, "assignees": [int(assignee_id)], "status": "A Fazer"}
    if due_date:
        data["due_date"] = due_date
    return _post(f"/list/{list_id}/task", data)


def atualizar_status_tarefa(task_id: str, status: str) -> dict:
    r = requests.put(f"{BASE}/task/{task_id}", headers=HEADERS, json={"status": status})
    r.raise_for_status()
    return r.json()
