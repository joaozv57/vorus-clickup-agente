from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from config import WHATSAPP_TO_MEMBER, MEMBERS, LIST_IDS, INTERNAL_SECRET
from clickup import (
    criar_relatorio_daily, get_tasks_socios,
    criar_tarefa_socios, criar_multiplas_tarefas,
    get_tasks_dia, encontrar_slots_livres,
    reagendar_tarefa, cancelar_tarefa, buscar_tarefa_por_nome,
)
from zapi import enviar_mensagem
from state import (
    get_estado, limpar_estado,
    set_aguardando_prioridades, set_aguardando_aprovacao,
    set_aguardando_fechamento, set_aguardando_reagendamento,
    get_aguardando_followup,
)
from claude_ai import interpretar_mensagem, organizar_prioridades, ajustar_prioridades
from messages import (
    msg_prioridades_organizadas, msg_semana_lancada,
    msg_followup, msg_erro_entendimento,
    msg_sugerir_reagendamento, msg_tarefa_reagendada, msg_tarefa_cancelada,
)
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
        return JSONResponse({"ok": False, "erro": "body invalido"}, status_code=400)

    numero   = body.get("phone") or body.get("from", "")
    texto    = (body.get("text", {}).get("message") or body.get("body") or "").strip()
    is_group = body.get("isGroup", False)

    if is_group or not numero or not texto:
        return JSONResponse({"ok": True})

    nome, dados = _identificar_membro(numero)
    if not nome:
        log.warning(f"Numero desconhecido: {numero}")
        return JSONResponse({"ok": True})

    log.info(f"Mensagem de {nome}: {texto[:80]}")

    estado       = get_estado(dados["whatsapp"])
    estado_tipo  = estado.get("tipo") if estado else None
    tarefas_info = get_tasks_socios(dados["lista_id"])
    pendentes    = tarefas_info.get("todas_pendentes", [])

    # --- Fluxo: aguardando prioridades (apos kickoff) ---
    if estado_tipo == "aguardando_prioridades":
        tarefas_org = organizar_prioridades(texto, nome)
        if not tarefas_org:
            enviar_mensagem(dados["whatsapp"], "Nao consegui organizar. Manda de novo?")
            return JSONResponse({"ok": True})
        set_aguardando_aprovacao(dados["whatsapp"], tarefas_org)
        enviar_mensagem(dados["whatsapp"], msg_prioridades_organizadas(nome, tarefas_org))
        return JSONResponse({"ok": True})

    # --- Fluxo: aguardando aprovacao da lista organizada ---
    if estado_tipo == "aguardando_aprovacao":
        intencao = interpretar_mensagem(texto, estado_atual="aguardando_aprovacao")
        intent   = intencao.get("intencao", "outro")

        if intent == "aprovacao":
            tarefas = estado.get("tarefas", [])
            criar_multiplas_tarefas(dados["lista_id"], tarefas, dados["clickup_id"])
            limpar_estado(dados["whatsapp"])
            enviar_mensagem(dados["whatsapp"], msg_semana_lancada(nome))
            return JSONResponse({"ok": True})

        if intent == "pedido_ajuste":
            tarefas_atuais  = estado.get("tarefas", [])
            tarefas_ajust   = ajustar_prioridades(texto, tarefas_atuais)
            set_aguardando_aprovacao(dados["whatsapp"], tarefas_ajust)
            enviar_mensagem(dados["whatsapp"], msg_prioridades_organizadas(nome, tarefas_ajust))
            return JSONResponse({"ok": True})

        enviar_mensagem(dados["whatsapp"], "Aprova a lista ou me diz o que ajustar?")
        return JSONResponse({"ok": True})

    # --- Fluxo: fechamento do dia ---
    if estado_tipo == "fechamento":
        concluidas    = estado.get("concluidas", [])
        nao_concluidas = estado.get("nao_concluidas", [])
        criar_relatorio_daily(
            nome=nome,
            concluidas=concluidas,
            nao_concluidas=nao_concluidas,
            resposta_wpp=texto,
        )
        limpar_estado(dados["whatsapp"])
        enviar_mensagem(dados["whatsapp"], f"Registrado. Boa noite, {nome}!")
        return JSONResponse({"ok": True})

    # --- Fluxo: aguardando escolha de reagendamento ---
    if estado_tipo == "aguardando_reagendamento":
        sugestoes  = estado.get("sugestoes", [])
        task_id    = estado.get("task_id")
        task_name  = estado.get("task_name", "Tarefa")
        escolha    = texto.strip()
        idx        = None
        if escolha in ("1", "2", "3"):
            idx = int(escolha) - 1
        elif "primeiro" in escolha.lower() or "opção 1" in escolha.lower():
            idx = 0
        elif "segundo" in escolha.lower() or "opção 2" in escolha.lower():
            idx = 1
        elif "terceiro" in escolha.lower() or "opção 3" in escolha.lower():
            idx = 2

        if idx is not None and idx < len(sugestoes):
            slot = sugestoes[idx]
            reagendar_tarefa(task_id, slot["start_ts"], slot["due_ts"])
            limpar_estado(dados["whatsapp"])
            data_fmt = slot["data"].strftime("%d/%m")
            enviar_mensagem(dados["whatsapp"], msg_tarefa_reagendada(task_name, data_fmt, slot["inicio"]))
        else:
            enviar_mensagem(dados["whatsapp"], "Responde com 1, 2 ou 3 para escolher o horário.")
        return JSONResponse({"ok": True})

    # --- Intencoes gerais ---
    intencao = interpretar_mensagem(texto, estado_atual=estado_tipo, tarefas_abertas=pendentes)
    intent   = intencao.get("intencao", "outro")

    log.info(f"  Intencao: {intent}")

    if intent == "criar_tarefa":
        nome_tarefa = intencao.get("nome_tarefa") or texto
        if not nome_tarefa or len(nome_tarefa) < 3:
            enviar_mensagem(dados["whatsapp"], "Qual o nome da tarefa?\nManda assim: tarefa: [descricao]")
            return JSONResponse({"ok": True})
        criar_tarefa_socios(dados["lista_id"], nome_tarefa, dados["clickup_id"])
        enviar_mensagem(dados["whatsapp"], f"Tarefa criada:\n  {nome_tarefa}")
        return JSONResponse({"ok": True})

    if intent == "nao_concluiu_tarefa":
        nome_tarefa = intencao.get("nome_tarefa") or texto
        tarefa = buscar_tarefa_por_nome(dados["lista_id"], nome_tarefa)
        if not tarefa:
            enviar_mensagem(dados["whatsapp"], f"Não encontrei a tarefa '{nome_tarefa}'. Pode confirmar o nome?")
            return JSONResponse({"ok": True})
        start_raw = tarefa.get("start_date")
        due_raw   = tarefa.get("due_date")
        duracao   = 60
        if start_raw and due_raw:
            duracao = max(30, (int(due_raw) - int(start_raw)) // 60000)
        janelas = dados.get("janelas_bloqueadas", {})
        sugestoes = encontrar_slots_livres(dados["lista_id"], duracao, janelas)
        set_aguardando_reagendamento(dados["whatsapp"], tarefa["id"], tarefa["name"], dados["lista_id"], sugestoes)
        enviar_mensagem(dados["whatsapp"], msg_sugerir_reagendamento(nome, tarefa["name"], sugestoes))
        return JSONResponse({"ok": True})

    if intent == "cancelar_tarefa":
        nome_tarefa = intencao.get("nome_tarefa") or texto
        tarefa = buscar_tarefa_por_nome(dados["lista_id"], nome_tarefa)
        if not tarefa:
            enviar_mensagem(dados["whatsapp"], f"Não encontrei a tarefa '{nome_tarefa}'. Pode confirmar o nome?")
            return JSONResponse({"ok": True})
        cancelar_tarefa(tarefa["id"])
        start_raw = tarefa.get("start_date")
        due_raw   = tarefa.get("due_date")
        duracao   = 60
        if start_raw and due_raw:
            duracao = max(30, (int(due_raw) - int(start_raw)) // 60000)
        janelas   = dados.get("janelas_bloqueadas", {})
        sugestoes = encontrar_slots_livres(dados["lista_id"], duracao, janelas)
        set_aguardando_reagendamento(dados["whatsapp"], tarefa["id"], tarefa["name"], dados["lista_id"], sugestoes)
        enviar_mensagem(dados["whatsapp"], msg_tarefa_cancelada(tarefa["name"], sugestoes))
        return JSONResponse({"ok": True})

    if intent == "ver_tarefas":
        if not pendentes:
            enviar_mensagem(dados["whatsapp"], "Voce nao tem tarefas abertas.")
        else:
            linhas = "\n".join([f"  {t['name']} [{t['status']['status'].upper()}]" for t in pendentes[:15]])
            enviar_mensagem(dados["whatsapp"], f"Suas tarefas abertas:\n{linhas}")
        return JSONResponse({"ok": True})

    enviar_mensagem(dados["whatsapp"], msg_erro_entendimento())
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
        job_pre_fechamento, job_fechamento, job_retrospectiva,
        job_wbr_prep, job_followup,
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
        "followup":       job_followup,
    }

    fn = jobs.get(job_name)
    if not fn:
        return JSONResponse({"ok": False, "erro": "job desconhecido"}, status_code=404)

    threading.Thread(target=fn, daemon=True).start()
    log.info(f"Job '{job_name}' disparado")
    return JSONResponse({"ok": True, "job": job_name})
