from datetime import date


def msg_kickoff(nome: str, tarefas: dict) -> str:
    pendentes = tarefas.get("todas_pendentes", [])
    if pendentes:
        linhas = "\n".join([f"  {t['name']}" for t in pendentes[:5]])
        ctx = f"Da semana passada ficaram em aberto:\n{linhas}\n\n"
    else:
        ctx = ""

    return (
        f"Vamos pra mais uma semana abencoada 🙏 {nome}!\n\n"
        f"{ctx}"
        "Me manda tudo que quer fazer essa semana. "
        "Pode mandar a vontade, sem formato, so listar mesmo.\n\n"
        "Eu organizo pra voce."
    )


def msg_prioridades_organizadas(nome: str, tarefas: list) -> str:
    linhas = "\n".join([
        f"  {t['nome']}" + (f" — {t['prazo']}" if t.get('prazo') else "")
        for t in tarefas
    ])
    return (
        f"Organizei sua semana assim:\n\n"
        f"{linhas}\n\n"
        "Aprova ou quer mudar alguma?"
    )


def msg_semana_lancada(nome: str) -> str:
    return f"Semana lancada no ClickUp. Bora, {nome}. 🚀"


def msg_pendencias_semana_anterior(nome: str, pendentes: list) -> str:
    linhas = "\n".join([f"  {t['name']}" for t in pendentes])
    return (
        f"Da semana passada ficaram em aberto:\n{linhas}\n\n"
        "Quer incluir alguma essa semana?"
    )


def msg_daily(nome: str, tarefas: dict) -> str:
    hoje = date.today().strftime("%d/%m")
    em_andamento = tarefas.get("em_andamento", [])
    planning = tarefas.get("planning", [])
    backlog = tarefas.get("backlog", [])
    bloqueadas = tarefas.get("bloqueadas", [])

    linhas = []
    if em_andamento:
        linhas.append("Continuando de ontem:")
        for t in em_andamento:
            linhas.append(f"  {t['name']}")
    if planning:
        linhas.append("\nPara iniciar:")
        for t in planning:
            linhas.append(f"  {t['name']}")
    if bloqueadas:
        linhas.append("\nBloqueadas:")
        for t in bloqueadas:
            linhas.append(f"  {t['name']}")
    if not linhas and backlog:
        linhas.append("Disponivel no backlog:")
        for t in backlog[:3]:
            linhas.append(f"  {t['name']}")

    agenda = "\n".join(linhas) if linhas else "Nenhuma tarefa aberta. Quer adicionar algo?"

    return (
        f"Bom dia, {nome}! Vamos pra mais um dia de vitoria 🚀\n\n"
        f"{agenda}\n\n"
        "O que voce vai atacar hoje?"
    )


def msg_checkin(nome: str, tarefas: dict) -> str:
    em_andamento = tarefas.get("em_andamento", [])
    bloqueadas = tarefas.get("bloqueadas", [])
    pendentes = tarefas.get("todas_pendentes", [])

    if not pendentes:
        return f"Checkin rapido, {nome}. Tudo concluido ate agora. Boa tarde!"

    linhas = []
    lista = em_andamento or pendentes[:4]
    for t in lista:
        linhas.append(f"  {t['name']}")

    msg = f"Checkin rapido, {nome}.\n\nAinda em aberto:\n" + "\n".join(linhas)

    if bloqueadas:
        msg += "\n\nTem tarefa bloqueada. Precisa de alguma coisa para destravar?"
    else:
        msg += "\n\nO que fechou ate agora? O que ficou em aberto?"

    return msg


def msg_fechamento(nome: str, tarefas: dict) -> str:
    pendentes = tarefas.get("todas_pendentes", [])

    if pendentes:
        linhas = "\n".join([f"  {t['name']}" for t in pendentes])
        planejado = f"Voce tinha em aberto:\n{linhas}\n\n"
    else:
        planejado = ""

    return (
        f"Fechamento do dia, {nome}.\n\n"
        f"{planejado}"
        "O que voce concluiu hoje?\n"
        "Tem algo bloqueado? (Tarefa bloqueada e aquela que depende de outra pessoa para avancar.)"
    )


def msg_retrospectiva(nome: str, tarefas: dict) -> str:
    concluidas = tarefas.get("concluidas", [])
    pendentes = tarefas.get("todas_pendentes", [])
    total = len(concluidas) + len(pendentes)
    pct = int(len(concluidas) / total * 100) if total > 0 else 0

    feitas = "\n".join([f"  {t['name']}" for t in concluidas]) or "  Nenhuma"
    abertas = "\n".join([f"  {t['name']}" for t in pendentes]) or "  Nenhuma"

    return (
        f"Chegamos ao final da semana! 🚀 Vamos fazer a retrospectiva, {nome}.\n\n"
        f"Planejadas: {total} / Concluidas: {len(concluidas)} ({pct}%)\n\n"
        f"Concluido:\n{feitas}\n\n"
        f"Em aberto:\n{abertas}\n\n"
        "Essas voltam pro backlog. Quer incluir alguma na semana que vem?\n\n"
        "O que travou essa semana e o que voce vai mover na proxima?"
    )


def msg_pre_fechamento(nome: str) -> str:
    return (
        f"{nome}, fechamento em 30 minutos.\n\n"
        "Vai organizando o que fez hoje. As 18h chego com o resumo e pergunto o que ficou de fora."
    )


def msg_wbr_prep(nome: str) -> str:
    return (
        f"{nome}, WBR amanha.\n\n"
        "Antes de fechar hoje, anota os seus numeros da semana:\n"
        "  Leads gerados\n"
        "  Propostas enviadas\n"
        "  Fechamentos\n"
        "  O que travou e o que vai mover na proxima semana\n\n"
        "Manda aqui quando tiver ou ja vai direto no ClickUp."
    )


def msg_followup() -> str:
    return "Passando pra lembrar de responder aqui 👆"


def msg_erro_entendimento() -> str:
    return (
        "Nao entendi. Voce pode:\n"
        "  Criar tarefa: 'tarefa: [descricao]'\n"
        "  Ver tarefas: 'minhas tarefas'"
    )
