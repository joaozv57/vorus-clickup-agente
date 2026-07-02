from datetime import date, datetime

_state: dict = {}


def _hoje():
    return date.today().isoformat()


def set_aguardando_prioridades(whatsapp: str):
    _state[whatsapp] = {
        "tipo": "aguardando_prioridades",
        "data": _hoje(),
        "enviado_em": datetime.now().isoformat(),
    }


def set_aguardando_aprovacao(whatsapp: str, tarefas: list):
    _state[whatsapp] = {
        "tipo": "aguardando_aprovacao",
        "data": _hoje(),
        "tarefas": tarefas,
        "enviado_em": datetime.now().isoformat(),
    }


def set_aguardando_fechamento(whatsapp: str, concluidas: list, nao_concluidas: list):
    _state[whatsapp] = {
        "tipo": "fechamento",
        "data": _hoje(),
        "concluidas": concluidas,
        "nao_concluidas": nao_concluidas,
        "enviado_em": datetime.now().isoformat(),
    }


def set_aguardando_tarefa(whatsapp: str, lista_id: str, lista_nome: str, assignee_id: str):
    _state[whatsapp] = {
        "tipo": "criar_tarefa",
        "data": _hoje(),
        "lista_id": lista_id,
        "lista_nome": lista_nome,
        "assignee_id": assignee_id,
    }


def get_estado(whatsapp: str) -> dict | None:
    estado = _state.get(whatsapp)
    if not estado:
        return None
    if estado.get("data") != _hoje():
        _state.pop(whatsapp, None)
        return None
    return estado


def limpar_estado(whatsapp: str):
    _state.pop(whatsapp, None)


def get_aguardando_followup() -> list[str]:
    """Retorna whatsapps com estado ativo e sem resposta por mais de 30 min."""
    now = datetime.now()
    resultado = []
    for wpp, estado in list(_state.items()):
        if estado.get("data") != _hoje():
            continue
        enviado = estado.get("enviado_em")
        if not enviado:
            continue
        minutos = (now - datetime.fromisoformat(enviado)).total_seconds() / 60
        if minutos >= 30:
            resultado.append(wpp)
    return resultado
