"""
Interpretação de linguagem natural via Claude API.
Classifica intenção de mensagens WhatsApp recebidas.
"""
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
    Interpreta mensagem de WhatsApp e retorna dict com intenção.

    Retorno:
        {
            "intencao": "criar_tarefa" | "ver_tarefas" | "resposta_daily" | "outro",
            "nome_tarefa": str | None,
            "conteudo": str
        }
    """
    if not ANTHROPIC_API_KEY:
        return _fallback_keywords(texto, estado_atual)

    ctx_estado  = f"Estado atual: {estado_atual}." if estado_atual else ""
    ctx_tarefas = ""
    if tarefas_abertas:
        nomes = [t["name"] for t in tarefas_abertas[:10]]
        ctx_tarefas = f"Tarefas abertas: {json.dumps(nomes, ensure_ascii=False)}."

    system = (
        "Você interpreta mensagens de WhatsApp de sócios de uma empresa "
        "integradas a um sistema de gestão de tarefas (ClickUp). "
        "Retorne APENAS JSON válido sem markdown.\n\n"
        "Intenções possíveis:\n"
        "- criar_tarefa: quer criar uma nova tarefa\n"
        "- ver_tarefas: quer ver suas tarefas abertas\n"
        "- resposta_daily: está respondendo ao fechamento/daily do dia\n"
        "- outro: não se encaixa\n\n"
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
        return json.loads(resp.content[0].text.strip())
    except Exception as e:
        log.warning(f"Claude AI falhou, usando fallback: {e}")
        return _fallback_keywords(texto, estado_atual)


def _fallback_keywords(texto: str, estado_atual: str = None) -> dict:
    t = texto.lower().strip()
    if estado_atual == "fechamento":
        return {"intencao": "resposta_daily", "nome_tarefa": None, "conteudo": texto}
    if t.startswith("tarefa") or "adiciona" in t or "cria" in t:
        nome = texto.split(":", 1)[-1].strip() if ":" in texto else texto
        return {"intencao": "criar_tarefa", "nome_tarefa": nome, "conteudo": texto}
    if any(p in t for p in ["minhas tarefas", "meu backlog", "o que tenho", "ver tarefas"]):
        return {"intencao": "ver_tarefas", "nome_tarefa": None, "conteudo": texto}
    return {"intencao": "outro", "nome_tarefa": None, "conteudo": texto}
