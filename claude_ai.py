import json
import logging
from config import ANTHROPIC_API_KEY

log = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        import anthropic
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def interpretar_mensagem(texto: str, estado_atual: str = None, tarefas_abertas: list = None) -> dict:
    """
    Intencoes: criar_tarefa | ver_tarefas | resposta_daily | aprovacao | pedido_ajuste | outro
    """
    if not ANTHROPIC_API_KEY:
        return _fallback_keywords(texto, estado_atual)

    ctx_estado = f"Estado atual da conversa: {estado_atual}." if estado_atual else ""
    ctx_tarefas = ""
    if tarefas_abertas:
        nomes = [t["name"] for t in tarefas_abertas[:10]]
        ctx_tarefas = f"Tarefas abertas: {json.dumps(nomes, ensure_ascii=False)}."

    system = (
        "Você interpreta mensagens de WhatsApp de sócios de uma empresa "
        "integradas a um sistema de gestão de tarefas.\n"
        "Retorne APENAS JSON válido sem markdown.\n\n"
        "Intencoes possiveis:\n"
        "- criar_tarefa: quer criar uma nova tarefa\n"
        "- ver_tarefas: quer ver suas tarefas abertas\n"
        "- nao_concluiu_tarefa: diz que nao fez ou nao conseguiu fazer uma tarefa (ex: 'nao fiz X', 'nao consegui X', 'ficou pra amanha X', 'nao terminei X')\n"
        "- cancelar_tarefa: diz que uma tarefa foi ou sera cancelada (ex: 'X foi cancelada', 'cancela X', 'vou cancelar X', 'precisarei cancelar X', 'nao vai rolar X', 'X nao acontece mais')\n"
        "- resposta_daily: respondendo ao fechamento/daily do dia\n"
        "- aprovacao: aprovando uma lista proposta (ex: 'aprova', 'ok', 'pode criar', 'sim', 'isso ai')\n"
        "- pedido_ajuste: quer ajustar a lista proposta (ex: 'muda X pra quarta', 'tira essa')\n"
        "- outro: nao se encaixa\n\n"
        "Formato: {\"intencao\": \"...\", \"nome_tarefa\": \"...\", \"conteudo\": \"...\"}"
    )

    user_msg = f"{ctx_estado} {ctx_tarefas}\nMensagem: \"{texto}\""

    try:
        client = _get_client()
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        resultado = json.loads(resp.content[0].text.strip())
        # se Claude retornou "outro", tenta keywords como segunda chance
        if resultado.get("intencao") == "outro":
            fb = _fallback_keywords(texto, estado_atual)
            if fb.get("intencao") != "outro":
                return fb
        return resultado
    except Exception as e:
        log.warning(f"Claude AI falhou, usando fallback: {e}")
        return _fallback_keywords(texto, estado_atual)


def organizar_prioridades(texto: str, nome: str) -> list:
    """
    Recebe texto livre com prioridades da semana.
    Retorna lista de dicts: [{nome: str, prazo: str}]
    """
    if not ANTHROPIC_API_KEY:
        return [{"nome": l.strip().lstrip("-*. "), "prazo": ""}
                for l in texto.split("\n") if l.strip()]

    system = (
        "Voce organiza prioridades semanais de um socio de empresa.\n"
        "O usuario mandou uma lista livre. Organize em tarefas claras com dia sugerido da semana.\n"
        "Retorne APENAS um array JSON. Exemplo:\n"
        "[{\"nome\": \"Finalizar proposta cliente X\", \"prazo\": \"quarta\"}, ...]\n"
        "Maximo 8 tarefas. Sem markdown. Sem explicacao."
    )

    try:
        client = _get_client()
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=system,
            messages=[{"role": "user", "content": f"Prioridades de {nome} para essa semana:\n{texto}"}],
        )
        return json.loads(resp.content[0].text.strip())
    except Exception as e:
        log.warning(f"organizar_prioridades falhou: {e}")
        return [{"nome": l.strip().lstrip("-*. "), "prazo": ""}
                for l in texto.split("\n") if l.strip()]


def ajustar_prioridades(texto_ajuste: str, tarefas_atuais: list) -> list:
    """Ajusta lista de tarefas conforme pedido do usuario."""
    if not ANTHROPIC_API_KEY:
        return tarefas_atuais

    system = (
        "Voce ajusta uma lista de tarefas semanais conforme pedido do usuario.\n"
        "Retorne APENAS o array JSON atualizado. Mesmo formato:\n"
        "[{\"nome\": \"...\", \"prazo\": \"...\"}, ...]\n"
        "Sem markdown. Sem explicacao."
    )

    user_msg = (
        f"Lista atual:\n{json.dumps(tarefas_atuais, ensure_ascii=False)}\n\n"
        f"Ajuste solicitado: {texto_ajuste}"
    )

    try:
        client = _get_client()
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        return json.loads(resp.content[0].text.strip())
    except Exception as e:
        log.warning(f"ajustar_prioridades falhou: {e}")
        return tarefas_atuais


def interpretar_resposta_checkin(texto: str, tarefas_manha: list, tarefas_tarde: list) -> dict:
    """
    Interpreta resposta livre ao checkin das 13h.
    Retorna: {canceladas: [nomes], bloqueadas: [nomes], tarde_ok: bool, positivo: bool}
    """
    nomes_manha = [t["name"] for t in tarefas_manha]
    nomes_tarde = [t["name"] for t in tarefas_tarde]

    system = (
        "Você interpreta respostas de texto livre de um executivo para um checkin de trabalho.\n"
        "Retorne APENAS JSON válido sem markdown.\n\n"
        "Analise a mensagem e identifique:\n"
        "- canceladas: lista de nomes de tarefas que foram canceladas ou não vão acontecer\n"
        "- bloqueadas: lista de nomes de tarefas que estão travadas por dependência externa\n"
        "- tarde_ok: true se a agenda da tarde está confirmada, false se há problema\n"
        "- positivo: true se a mensagem indica que a manhã correu bem de forma geral\n\n"
        "Se uma tarefa cancelada bater parcialmente com um nome da lista, use o nome exato da lista.\n"
        "Formato: {\"canceladas\": [...], \"bloqueadas\": [...], \"tarde_ok\": true, \"positivo\": true}"
    )

    user_msg = (
        f"Tarefas da manhã: {json.dumps(nomes_manha, ensure_ascii=False)}\n"
        f"Tarefas da tarde: {json.dumps(nomes_tarde, ensure_ascii=False)}\n\n"
        f"Resposta do executivo: \"{texto}\""
    )

    try:
        client = _get_client()
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        return json.loads(resp.content[0].text.strip())
    except Exception as e:
        log.warning(f"interpretar_resposta_checkin falhou: {e}")
        return {"canceladas": [], "bloqueadas": [], "tarde_ok": True, "positivo": True}


def _fallback_keywords(texto: str, estado_atual: str = None) -> dict:
    t = texto.lower().strip()
    if estado_atual == "fechamento":
        return {"intencao": "resposta_daily", "nome_tarefa": None, "conteudo": texto}
    if estado_atual == "aguardando_aprovacao":
        if any(p in t for p in ["aprova", "ok", "pode", "sim", "isso", "tudo certo", "bora"]):
            return {"intencao": "aprovacao", "nome_tarefa": None, "conteudo": texto}
        return {"intencao": "pedido_ajuste", "nome_tarefa": None, "conteudo": texto}
    if t.startswith("tarefa") or "adiciona" in t or "cria" in t:
        nome = texto.split(":", 1)[-1].strip() if ":" in texto else texto
        return {"intencao": "criar_tarefa", "nome_tarefa": nome, "conteudo": texto}
    if any(p in t for p in ["minhas tarefas", "meu backlog", "o que tenho", "ver tarefas"]):
        return {"intencao": "ver_tarefas", "nome_tarefa": None, "conteudo": texto}
    if any(p in t for p in ["nao fiz", "não fiz", "nao consegui", "não consegui", "ficou pra amanha", "ficou pra amanhã"]):
        return {"intencao": "nao_concluiu_tarefa", "nome_tarefa": None, "conteudo": texto}
    if any(p in t for p in ["cancelad", "cancela", "cancelar", "nao vai rolar", "não vai rolar", "nao acontece", "não acontece"]):
        return {"intencao": "cancelar_tarefa", "nome_tarefa": None, "conteudo": texto}
    return {"intencao": "outro", "nome_tarefa": None, "conteudo": texto}
