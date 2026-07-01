"""
Recebe mensagens do WhatsApp via Z-API webhook.
Usa Claude AI para interpretar intenção e age no ClickUp.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from config import WHATSAPP_TO_MEMBER, MEMBERS, LIST_IDS, INTERNAL_SECRET
from clickup import criar_relatorio_daily, get_tasks_socios, criar_tarefa_socios
from zapi import enviar_mensagem
from state import get_estado, limpar_estado
from claude_ai import interpretar_mensagem

from api_dashboard import router as dashboard_router

log = logging.getLogger(__name__)
app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(dashboard_router)


def _numero_limpo(numero: str) -> str:
    return "".join(filter(str.isdigit, numero))


def _identificar_membro(numero: str):
    limpo = _numero_limpo(numero)
    for wpp, nome in WHATSAPP_TO_MEMBER.items():
        if _numero_limpo(wpp) in limpo or limpo in _numero_limpo(wpp):
            return nome, MEMBERS[nome]
    return None, None


@app.post("/webhook")
async def webhook(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "erro": "body inválido"}, status_code=400)

    numero   = body.get("phone") or body.get("from", "")
    texto    = (body.get("text", {}).get("message") or body.get("body") or "").strip()
    is_group = body.get("isGroup", False)

    if is_group or not numero or not texto:
        return JSONResponse({"ok": True})

    nome, dados = _identificar_membro(numero)
    if not nome:
        log.warning(f"Número desconhecido: {numero}")
        return JSONResponse({"ok": True})

    log.info(f"Mensagem de {nome}: {texto[:60]}")

    estado = get_estado(dados["whatsapp"])
    estado_tipo = estado.get("tipo") if estado else None

    tarefas_abertas = get_tasks_socios(dados["lista_id"]).get("todas_pendentes", [])
    intencao = interpretar_mensagem(texto, estado_atual=estado_tipo, tarefas_abertas=tarefas_abertas)
    intent = intencao.get("intencao", "outro")

    log.info(f"  Intenção: {intent}")

    if intent == "resposta_daily" or estado_tipo == "fechamento":
        concluidas    = estado.get("concluidas", []) if estado else []
        nao_concluidas = estado.get("nao_concluidas", []) if estado else []
        criar_relatorio_daily(
            nome=nome,
            concluidas=concluidas,
            nao_concluidas=nao_concluidas,
            resposta_wpp=texto,
        )
        limpar_estado(dados["whatsapp"])
        enviar_mensagem(dados["whatsapp"], f"Daily registrada. Boa noite, {nome}.")
        return JSONResponse({"ok": True})

    if intent == "criar_tarefa":
        nome_tarefa = intencao.get("nome_tarefa") or texto
        if not nome_tarefa or len(nome_tarefa) < 3:
            enviar_mensagem(dados["whatsapp"], "Qual o nome da tarefa? Me manda assim:\ntarefa: [descrição]")
            return JSONResponse({"ok": True})
        criar_tarefa_socios(
            lista_id=dados["lista_id"],
            nome=nome_tarefa,
            assignee_id=dados["clickup_id"],
        )
        enviar_mensagem(dados["whatsapp"], f"Tarefa criada:\n  • {nome_tarefa}")
        return JSONResponse({"ok": True})

    if intent == "ver_tarefas":
        tarefas = get_tasks_socios(dados["lista_id"])
        pendentes = tarefas["todas_pendentes"]
        if not pendentes:
            enviar_mensagem(dados["whatsapp"], "Você não tem tarefas abertas.")
        else:
            linhas = "\n".join([f"  • {t['name']} [{t['status']['status'].upper()}]" for t in pendentes[:15]])
            enviar_mensagem(dados["whatsapp"], f"Suas tarefas abertas:\n{linhas}")
        return JSONResponse({"ok": True})

    enviar_mensagem(
        dados["whatsapp"],
        "Não entendi. Você pode:\n"
        "  • Criar tarefa: 'tarefa: [descrição]'\n"
        "  • Ver tarefas: 'minhas tarefas'"
    )
    return JSONResponse({"ok": True})


@app.get("/health")
def health():
    return {"status": "ok"}


def _auth_interna(request: Request) -> bool:
    return request.headers.get("Authorization", "") == f"Bearer {INTERNAL_SECRET}"


@app.post("/internal/job/{job_name}")
async def run_job_interno(job_name: str, request: Request):
    if not _auth_interna(request):
        return JSONResponse({"ok": False}, status_code=401)

    from scheduler import (
        job_kickoff, job_daily, job_checkin,
        job_pre_fechamento, job_fechamento, job_retrospectiva, job_wbr_prep,
    )
    import threading

    jobs = {
        "kickoff":        job_kickoff,
        "daily":          job_daily,
        "checkin":        job_checkin,
        "pre-fechamento": job_pre_fechamento,
        "fechamento":     job_fechamento,
        "retrospectiva":  job_retrospectiva,
        "wbr-prep":       job_wbr_prep,
    }

    fn = jobs.get(job_name)
    if not fn:
        return JSONResponse({"ok": False, "erro": "job desconhecido"}, status_code=404)

    threading.Thread(target=fn, daemon=True).start()
    log.info(f"Job '{job_name}' disparado")
    return JSONResponse({"ok": True, "job": job_name})
