from datetime import date


def msg_kickoff(nome: str, tarefas: dict) -> str:
    hoje = date.today().strftime("%d/%m")
    em_andamento = tarefas.get("em_andamento", [])
    planning     = tarefas.get("planning", [])
    backlog      = tarefas.get("backlog", [])
    bloqueadas   = tarefas.get("bloqueadas", [])

    linhas = []
    if em_andamento:
        linhas.append("Em andamento:")
        for t in em_andamento:
            linhas.append(f"  • {t['name']}")
    if planning:
        linhas.append("\nEm planejamento:")
        for t in planning:
            linhas.append(f"  • {t['name']}")
    if backlog:
        linhas.append("\nBacklog:")
        for t in backlog[:5]:
            linhas.append(f"  • {t['name']}")
        if len(backlog) > 5:
            linhas.append(f"  ... e mais {len(backlog) - 5}")
    if bloqueadas:
        linhas.append("\nBloqueadas:")
        for t in bloqueadas:
            linhas.append(f"  • {t['name']}")

    resumo = "\n".join(linhas) if linhas else "Nenhuma tarefa registrada ainda."

    return (
        f"Boa semana, {nome}. Kickoff de segunda ({hoje}).\n\n"
        f"{resumo}\n\n"
        "Quais são suas 3 prioridades desta semana? Me manda aqui."
    )


def msg_daily(nome: str, tarefas: dict) -> str:
    hoje = date.today().strftime("%d/%m")
    em_andamento = tarefas.get("em_andamento", [])
    planning     = tarefas.get("planning", [])
    backlog      = tarefas.get("backlog", [])
    bloqueadas   = tarefas.get("bloqueadas", [])

    linhas = []
    if em_andamento:
        linhas.append("Continuando hoje:")
        for t in em_andamento:
            linhas.append(f"  • {t['name']}")
    if planning:
        linhas.append("\nPara iniciar:")
        for t in planning:
            linhas.append(f"  • {t['name']}")
    if bloqueadas:
        linhas.append("\nBloqueadas (precisam atenção):")
        for t in bloqueadas:
            linhas.append(f"  • {t['name']}")
    if not linhas and backlog:
        linhas.append("Backlog disponível:")
        for t in backlog[:3]:
            linhas.append(f"  • {t['name']}")

    agenda = "\n".join(linhas) if linhas else "Nenhuma tarefa para hoje — quer adicionar algo?"

    return f"Bom dia, {nome}. Daily de hoje ({hoje}):\n\n{agenda}\n\nBora."


def msg_checkin(nome: str, tarefas: dict) -> str:
    em_andamento = tarefas.get("em_andamento", [])
    bloqueadas   = tarefas.get("bloqueadas", [])
    pendentes    = tarefas.get("todas_pendentes", [])

    if not pendentes:
        return f"{nome}, tudo concluído até agora. Boa tarde."

    linhas = []
    if em_andamento:
        for t in em_andamento:
            linhas.append(f"  • {t['name']}")
    elif pendentes:
        for t in pendentes[:4]:
            linhas.append(f"  • {t['name']}")

    lista = "\n".join(linhas)
    msg = f"{nome}, check-in da tarde.\n\nAinda em aberto:\n{lista}"

    if bloqueadas:
        msg += "\n\nTem tarefa bloqueada — precisa de alguma coisa para destravar?"
    else:
        msg += "\n\nComo está o andamento?"

    return msg


def msg_retrospectiva(nome: str, tarefas: dict) -> str:
    concluidas = tarefas.get("concluidas", [])
    pendentes  = tarefas.get("todas_pendentes", [])

    feitas  = "\n".join([f"  ✓ {t['name']}" for t in concluidas]) or "  Nenhuma"
    abertas = "\n".join([f"  ○ {t['name']}" for t in pendentes]) or "  Nenhuma"

    return (
        f"Fechando a semana, {nome}.\n\n"
        f"Concluído:\n{feitas}\n\n"
        f"Em aberto para a próxima:\n{abertas}\n\n"
        "O que travou essa semana e o que você vai mover na próxima?"
    )


def msg_fechamento(nome: str, tarefas: dict) -> str:
    concluidas    = tarefas.get("concluidas", [])
    nao_concluidas = tarefas.get("todas_pendentes", [])

    linhas_feitas    = "\n".join([f"  ✓ {t['name']}" for t in concluidas]) or "  Nenhuma"
    linhas_pendentes = "\n".join([f"  ✗ {t['name']}" for t in nao_concluidas]) or "  Nenhuma"

    msg = f"Fechando o dia, {nome}.\n\nConcluído:\n{linhas_feitas}\n\nNão concluído:\n{linhas_pendentes}\n"

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


def msg_tarefa_criada(nome_tarefa: str, lista: str = "") -> str:
    return f"Tarefa criada no ClickUp:\n  • {nome_tarefa}"


def msg_erro_entendimento() -> str:
    return (
        "Não entendi. Você pode:\n"
        "  • Criar tarefa: 'tarefa: [descrição]'\n"
        "  • Ver tarefas: 'minhas tarefas'"
    )
