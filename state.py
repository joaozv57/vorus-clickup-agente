"""
Gerencia o estado da conversa: quem está aguardando resposta do fechamento.
Persiste em JSON simples (3 pessoas, sem necessidade de banco de dados).
"""
import json
import os
from datetime import date

STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")


def _load() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE) as f:
        return json.load(f)


def _save(data: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def set_aguardando_fechamento(whatsapp: str, concluidas: list, nao_concluidas: list):
    """Marca que estamos aguardando a resposta de fechamento do membro."""
    data = _load()
    data[whatsapp] = {
        "tipo": "fechamento",
        "data": str(date.today()),
        "concluidas": concluidas,
        "nao_concluidas": nao_concluidas,
    }
    _save(data)


def get_estado(whatsapp: str) -> dict | None:
    """Retorna o estado atual do membro ou None se não há nada pendente."""
    data = _load()
    estado = data.get(whatsapp)
    if not estado:
        return None
    # Limpa estados de dias anteriores
    if estado.get("data") != str(date.today()):
        limpar_estado(whatsapp)
        return None
    return estado


def limpar_estado(whatsapp: str):
    data = _load()
    data.pop(whatsapp, None)
    _save(data)


def set_aguardando_tarefa(whatsapp: str, lista_id: str, lista_nome: str, assignee_id: str):
    """Marca que o membro mandou um comando de criar tarefa e aguardamos confirmação."""
    data = _load()
    data[whatsapp] = {
        "tipo": "criar_tarefa",
        "data": str(date.today()),
        "lista_id": lista_id,
        "lista_nome": lista_nome,
        "assignee_id": assignee_id,
    }
    _save(data)
