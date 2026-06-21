"""
Estado em memória: rastreia quem está aguardando resposta de fechamento.
Dura enquanto o processo estiver vivo — suficiente para a janela de ~1h entre o
envio do fechamento (18h) e a resposta da pessoa.
"""
from datetime import date

_state: dict = {}


def set_aguardando_fechamento(whatsapp: str, concluidas: list, nao_concluidas: list):
    _state[whatsapp] = {
        "tipo": "fechamento",
        "data": date.today().isoformat(),
        "concluidas": concluidas,
        "nao_concluidas": nao_concluidas,
    }


def get_estado(whatsapp: str) -> dict | None:
    estado = _state.get(whatsapp)
    if not estado:
        return None
    if estado.get("data") != date.today().isoformat():
        _state.pop(whatsapp, None)
        return None
    return estado


def limpar_estado(whatsapp: str):
    _state.pop(whatsapp, None)


def set_aguardando_tarefa(whatsapp: str, lista_id: str, lista_nome: str, assignee_id: str):
    _state[whatsapp] = {
        "tipo": "criar_tarefa",
        "data": date.today().isoformat(),
        "lista_id": lista_id,
        "lista_nome": lista_nome,
        "assignee_id": assignee_id,
    }
