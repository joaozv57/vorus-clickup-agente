from datetime import date


def _fmt(t: dict, com_hora: bool = False) -> str:
    """Formata uma tarefa com bullets de descrição."""
    prefixo = f"  {t['start_dt'].strftime('%H:%M')} " if com_hora else "  "
    linha = f"{prefixo}{t['name']}"
    for b in t["bullets"]:
        linha += f"\n    · {b}"
    return linha


def _bloco(tarefas: list, com_hora: bool = False) -> str:
    return "\n".join(_fmt(t, com_hora) for t in tarefas)


# ── Mensagens de abertura do dia ─────────────────────────────────────────────

def msg_kickoff(nome: str, tarefas_dia: list) -> str:
    """Segunda-feira — abre com semana abençoada."""
    corpo = _bloco(tarefas_dia, com_hora=True) or "  Nenhuma tarefa programada."
    return (
        f"Vamos pra mais uma semana abençoada 🙏 {nome}!\n\n"
        f"O que temos programado para hoje:\n\n"
        f"{corpo}\n\n"
        "Tem algo importante que não está aqui e quer adicionar?"
    )


def msg_daily(nome: str, tarefas_dia: list) -> str:
    """Terça a sexta — abertura padrão do dia."""
    corpo = _bloco(tarefas_dia, com_hora=True) or "  Nenhuma tarefa programada."
    return (
        f"Bom dia, {nome}!\n\n"
        f"O que temos programado para hoje:\n\n"
        f"{corpo}\n\n"
        "Tem algo importante que não está aqui e quer adicionar?"
    )


# ── Check-in 13h — só tarefas com fim ≤ 13h ─────────────────────────────────

def msg_checkin(nome: str, tarefas_dia: list) -> str:
    manha = [
        t for t in tarefas_dia
        if t["due_dt"].hour < 13 or (t["due_dt"].hour == 13 and t["due_dt"].minute == 0)
    ]
    if not manha:
        return f"Checkin rápido, {nome}. Nada programado para a manhã."
    corpo = _bloco(manha)
    return (
        f"Checkin rápido, {nome}.\n\n"
        f"Me atualiza sobre essas tarefas:\n\n"
        f"{corpo}\n\n"
        "O que fechou? O que ficou em aberto?"
    )


# ── Pré-fechamento 17h30 — só tarefas com fim > 13h ──────────────────────────

def msg_pre_fechamento(nome: str, tarefas_dia: list) -> str:
    tarde = [
        t for t in tarefas_dia
        if t["due_dt"].hour > 13 or (t["due_dt"].hour == 13 and t["due_dt"].minute > 0)
    ]
    if not tarde:
        return f"{nome}, daqui a pouco fechamos o dia. Boa tarde!"
    corpo = _bloco(tarde)
    return (
        f"{nome}, daqui a pouco fechamos o dia.\n\n"
        f"Como ficou a tarde?\n\n"
        f"{corpo}\n\n"
        "Conseguiu fechar? Tem algo que precisa passar pra amanhã?"
    )


# ── Fechamento 18h — todas as tarefas do dia ─────────────────────────────────

def msg_fechamento(nome: str, tarefas_dia: list) -> str:
    if not tarefas_dia:
        return (
            f"Fechamento do dia, {nome}.\n\n"
            "O que você concluiu hoje?\n"
            "Tem algo bloqueado? (Tarefa bloqueada é aquela que depende de outra pessoa para avançar.)"
        )
    corpo = _bloco(tarefas_dia)
    return (
        f"Fechamento do dia, {nome}.\n\n"
        f"Você tinha em aberto:\n"
        f"{corpo}\n\n"
        "O que você concluiu hoje?\n"
        "Tem algo bloqueado? (Tarefa bloqueada é aquela que depende de outra pessoa para avançar.)"
    )


# ── Retrospectiva sexta 18h ───────────────────────────────────────────────────

def msg_retrospectiva(nome: str, tarefas: dict) -> str:
    concluidas = tarefas.get("concluidas", [])
    pendentes  = tarefas.get("todas_pendentes", [])
    total = len(concluidas) + len(pendentes)
    pct   = int(len(concluidas) / total * 100) if total > 0 else 0

    feitas  = "\n".join(f"  {t['name']}" for t in concluidas) or "  Nenhuma"
    abertas = "\n".join(f"  {t['name']}" for t in pendentes)  or "  Nenhuma"

    return (
        f"Chegamos ao final da semana! 🚀 Vamos fazer a retrospectiva, {nome}.\n\n"
        f"Planejadas: {total} / Concluídas: {len(concluidas)} ({pct}%)\n\n"
        f"Concluído:\n{feitas}\n\n"
        f"Em aberto:\n{abertas}\n\n"
        "Essas voltam pro backlog. Quer incluir alguma na semana que vem?\n\n"
        "O que travou essa semana e o que você vai mover na próxima?"
    )


# ── WBR prep sexta 17h ───────────────────────────────────────────────────────

def msg_wbr_prep(nome: str) -> str:
    return (
        f"{nome}, WBR amanhã.\n\n"
        "Antes de fechar hoje, anota os seus números da semana:\n"
        "  Leads gerados\n"
        "  Propostas enviadas\n"
        "  Fechamentos\n"
        "  O que travou e o que vai mover na próxima semana\n\n"
        "Manda aqui quando tiver ou já vai direto no ClickUp."
    )


# ── Utilitários ──────────────────────────────────────────────────────────────

def msg_semana_lancada(nome: str) -> str:
    return f"Semana lançada no ClickUp. Bora, {nome}. 🚀"


def msg_followup() -> str:
    return "Passando pra lembrar de responder aqui 👆"


def msg_erro_entendimento() -> str:
    return (
        "Não entendi. Você pode:\n"
        "  Criar tarefa: 'tarefa: [descrição]'\n"
        "  Ver tarefas: 'minhas tarefas'"
    )


def msg_sugerir_reagendamento(nome: str, task_name: str, sugestoes: list) -> str:
    DIAS_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    if not sugestoes:
        return (
            f"{nome}, não encontrei horário livre nos próximos dias para {task_name}.\n"
            "Quer que eu verifique mais pra frente?"
        )
    linhas = "\n".join(
        f"  {i}. {DIAS_PT[s['data'].weekday()]} {s['data'].strftime('%d/%m')} às {s['inicio']}"
        for i, s in enumerate(sugestoes, 1)
    )
    return (
        f"{task_name} não foi feito hoje.\n\n"
        f"Encontrei esses horários disponíveis:\n\n"
        f"{linhas}\n\n"
        "Qual prefere? Responde com o número (1 a 5)."
    )


def msg_tarefa_reagendada(task_name: str, data: str, inicio: str) -> str:
    return f"{task_name} reagendado para {data} às {inicio}."


def msg_tarefa_cancelada(task_name: str, sugestoes: list = None) -> str:
    DIAS_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    if not sugestoes:
        return (
            f"{task_name} cancelada.\n\n"
            "Não encontrei horário livre nos próximos dias para remarcar.\n"
            "Quer que eu verifique mais pra frente?"
        )
    linhas = "\n".join(
        f"  {i}. {DIAS_PT[s['data'].weekday()]} {s['data'].strftime('%d/%m')} às {s['inicio']}"
        for i, s in enumerate(sugestoes, 1)
    )
    return (
        f"{task_name} cancelada.\n\n"
        f"Quer remarcar? Encontrei esses horários:\n\n"
        f"{linhas}\n\n"
        "Qual prefere? Responde com o número (1 a 5)."
    )


def msg_prioridades_organizadas(nome: str, tarefas: list) -> str:
    linhas = "\n".join([
        f"  {t['nome']}" + (f" — {t['prazo']}" if t.get("prazo") else "")
        for t in tarefas
    ])
    return (
        f"Organizei assim:\n\n"
        f"{linhas}\n\n"
        "Aprova ou quer mudar alguma?"
    )
