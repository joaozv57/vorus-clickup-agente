from datetime import date


def msg_manha(nome: str, tarefas: dict) -> str:
    hoje = date.today().strftime("%d/%m")
    a_fazer = tarefas.get("a_fazer", [])
    em_andamento = tarefas.get("em_andamento", [])
    bloqueadas = tarefas.get("bloqueadas", [])

    linhas = []

    if a_fazer:
        linhas.append("Para fazer hoje:")
        for t in a_fazer:
            linhas.append(f"  • {t['name']}")

    if em_andamento:
        linhas.append("\nContinuando:")
        for t in em_andamento:
            linhas.append(f"  • {t['name']}")

    if bloqueadas:
        linhas.append("\nBloqueadas (precisam de atenção):")
        for t in bloqueadas:
            linhas.append(f"  • {t['name']}")

    if not linhas:
        linhas.append("Nenhuma tarefa registrada para hoje.")
        linhas.append("Se quiser adicionar, é só me mandar aqui.")

    agenda = "\n".join(linhas)

    return f"""Bom dia, {nome}. Agenda de hoje ({hoje}):

{agenda}

Bora."""


def msg_tarde(nome: str, tarefas: dict) -> str:
    pendentes = tarefas.get("todas_pendentes", [])

    if not pendentes:
        return f"{nome}, tudo das tarefas de hoje está concluído. Boa tarde."

    linhas = "\n".join([f"  • {t['name']}" for t in pendentes])

    return f"""{nome}, passando pra checar.

Ainda em aberto:
{linhas}

Precisa de alguma coisa para destravar?"""


def msg_fechamento(nome: str, tarefas: dict) -> str:
    concluidas = tarefas.get("concluidas", [])
    nao_concluidas = tarefas.get("todas_pendentes", [])

    linhas_feitas = "\n".join([f"  ✓ {t['name']}" for t in concluidas]) or "  Nenhuma"
    linhas_pendentes = "\n".join([f"  ✗ {t['name']}" for t in nao_concluidas]) or "  Nenhuma"

    msg = f"""Fechando o dia, {nome}.

Concluído:
{linhas_feitas}

Não concluído:
{linhas_pendentes}
"""

    if nao_concluidas:
        msg += "\nO que impediu e o que você fará amanhã para mover o ponteiro?"
    else:
        msg += "\nDia completo. O que você fará amanhã para mover o ponteiro?"

    return msg


def msg_pre_fechamento(nome: str) -> str:
    return (
        f"{nome}, fechamento em 30 minutos.\n\n"
        "Vai organizando o que fez hoje. Às 18h chego com o resumo do ClickUp e pergunto o que ficou de fora."
    )


def msg_wbr_prep(nome: str) -> str:
    return (
        f"{nome}, WBR amanhã.\n\n"
        "Antes de fechar hoje, anota os seus números da semana:\n"
        "  • Leads gerados\n"
        "  • Propostas enviadas\n"
        "  • Fechamentos\n"
        "  • O que travou e o que vai mover na próxima semana\n\n"
        "Manda aqui quando tiver ou já vai direto no ClickUp."
    )


def msg_tarefa_criada(nome_tarefa: str, lista: str) -> str:
    return f"Tarefa criada no ClickUp:\n  • {nome_tarefa}\n  Lista: {lista}"


def msg_erro_entendimento() -> str:
    return (
        "Não entendi o comando. Você pode:\n"
        "  • Criar tarefa: 'tarefa: [descrição]'\n"
        "  • Criar tarefa em lista específica: 'tarefa em pipeline: [descrição]'\n"
        "  • Ver tarefas: 'minhas tarefas'"
    )
