"""
Recebe mensagens do WhatsApp via Z-API webhook.
Processa comandos e respostas de fechamento.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from config import WHATSAPP_TO_MEMBER, MEMBERS, LIST_IDS, INTERNAL_SECRET
from clickup import criar_relatorio_daily, criar_tarefa, get_todas_tarefas_membro
from messages import msg_tarefa_criada, msg_erro_entendimento
from zapi import enviar_mensagem
from state import get_estado, limpar_estado, set_aguardando_tarefa

from api_dashboard import router as dashboard_router

log = logging.getLogger(__name__)
app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(dashboard_router)

# Mapeamento de palavras-chave para listas
LISTA_KEYWORDS = {
    "pipeline":     (LIST_IDS["pipeline"], "Pipeline Comercial"),
    "campanha":     (LIST_IDS["campanhas"], "Campanhas Ativas"),
    "campanha":     (LIST_IDS["campanhas"], "Campanhas Ativas"),
    "projeto":      (LIST_IDS["projetos_ativos"], "Projetos Ativos"),
    "automação":    (LIST_IDS["projetos_ativos"], "Automações"),
    "automacao":    (LIST_IDS["projetos_ativos"], "Automações"),
}


def _numero_limpo(numero: str) -> str:
    return "".join(filter(str.isdigit, numero))


def _identificar_membro(numero: str):
    limpo = _numero_limpo(numero)
    for wpp, nome in WHATSAPP_TO_MEMBER.items():
        if _numero_limpo(wpp) in limpo or limpo in _numero_limpo(wpp):
            return nome, MEMBERS[nome]
    return None, None


def _processar_comando(texto: str, nome: str, dados: dict) -> bool:
    """
    Processa comandos vindos do WhatsApp.
    Retorna True se processou, False se não reconheceu.
    """
    texto_lower = texto.lower().strip()

    # Criar tarefa: "tarefa: descrição" ou "tarefa em pipeline: descrição"
    if texto_lower.startswith("tarefa"):
        lista_id = LIST_IDS["projetos_ativos"]
        lista_nome = "Projetos Ativos"

        # Verificar se especificou lista
        for keyword, (lid, lnome) in LISTA_KEYWORDS.items():
            if keyword in texto_lower:
                lista_id = lid
                lista_nome = lnome
                break

        # Extrair nome da tarefa
        partes = texto.split(":", 1)
        if len(partes) < 2 or not partes[1].strip():
            enviar_mensagem(dados["whatsapp"], "Qual o nome da tarefa? Me manda assim:\ntarefa: [descrição da tarefa]")
            return True

        nome_tarefa = partes[1].strip()
        criar_tarefa(
            list_id=lista_id,
            nome=nome_tarefa,
            descricao="",
            assignee_id=dados["clickup_id"],
        )
        enviar_mensagem(dados["whatsapp"], msg_tarefa_criada(nome_tarefa, lista_nome))
        return True

    # Ver tarefas abertas
    if any(p in texto_lower for p in ["minhas tarefas", "meu backlog", "o que tenho"]):
        tarefas = get_todas_tarefas_membro(dados["clickup_id"])
        if not tarefas:
            enviar_mensagem(dados["whatsapp"], "Você não tem tarefas abertas no momento.")
        else:
            linhas = "\n".join([f"  • {t['name']} [{t['status']['status']}]" for t in tarefas[:15]])
            enviar_mensagem(dados["whatsapp"], f"Suas tarefas abertas:\n{linhas}")
        return True

    return False


@app.post("/webhook")
async def webhook(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "erro": "body inválido"}, status_code=400)

    # Estrutura Z-API
    numero = body.get("phone") or body.get("from", "")
    texto = (body.get("text", {}).get("message") or body.get("body") or "").strip()
    is_group = body.get("isGroup", False)

    if is_group or not numero or not texto:
        return JSONResponse({"ok": True})

    nome, dados = _identificar_membro(numero)
    if not nome:
        log.warning(f"Número desconhecido: {numero}")
        return JSONResponse({"ok": True})

    log.info(f"Mensagem de {nome}: {texto[:60]}")

    # 1. Verificar se há estado pendente (resposta de fechamento)
    estado = get_estado(dados["whatsapp"])
    if estado and estado.get("tipo") == "fechamento":
        # A resposta é o motivo/plano de amanhã
        concluidas = estado.get("concluidas", [])
        nao_concluidas = estado.get("nao_concluidas", [])

        criar_relatorio_daily(
            nome=nome,
            concluidas=concluidas,
            nao_concluidas=nao_concluidas,
            resposta_wpp=texto,
        )
        limpar_estado(dados["whatsapp"])

        enviar_mensagem(dados["whatsapp"], f"Daily registrada no ClickUp. Boa noite, {nome}.")
        log.info(f"Daily de {nome} salva no ClickUp")
        return JSONResponse({"ok": True})

    # 2. Processar comandos
    processou = _processar_comando(texto, nome, dados)
    if not processou:
        enviar_mensagem(dados["whatsapp"], msg_erro_entendimento())

    return JSONResponse({"ok": True})


@app.get("/health")
def health():
    return {"status": "ok"}


# ── Endpoints internos (chamados pelo GitHub Actions) ────────────────────────

def _auth_interna(request: Request) -> bool:
    token = request.headers.get("Authorization", "")
    return token == f"Bearer {INTERNAL_SECRET}"


@app.post("/internal/job/{job_name}")
async def run_job_interno(job_name: str, request: Request):
    if not _auth_interna(request):
        return JSONResponse({"ok": False}, status_code=401)

    from scheduler import job_manha, job_tarde, job_pre_fechamento, job_fechamento, job_wbr_prep
    import threading

    jobs = {
        "manha":           job_manha,
        "tarde":           job_tarde,
        "pre-fechamento":  job_pre_fechamento,
        "fechamento":      job_fechamento,
        "wbr-prep":        job_wbr_prep,
    }

    fn = jobs.get(job_name)
    if not fn:
        return JSONResponse({"ok": False, "erro": "job desconhecido"}, status_code=404)

    threading.Thread(target=fn, daemon=True).start()
    log.info(f"Job '{job_name}' disparado via Actions")
    return JSONResponse({"ok": True, "job": job_name})
