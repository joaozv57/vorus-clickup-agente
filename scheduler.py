import schedule
import time
import logging
from config import (
    MEMBERS, TEST_MODE, TEST_WHATSAPP,
    HORARIO_KICKOFF, HORARIO_DAILY, HORARIO_CHECKIN,
    HORARIO_PRE_FECHAMENTO, HORARIO_FECHAMENTO, HORARIO_RETROSPECTIVA,
    HORARIO_WBR_PREP,
)
from clickup import get_tasks_socios, criar_relatorio_daily
from messages import (
    msg_kickoff, msg_daily, msg_checkin,
    msg_pre_fechamento, msg_fechamento, msg_retrospectiva, msg_wbr_prep,
)
from zapi import enviar_mensagem
from state import set_aguardando_prioridades, set_aguardando_fechamento, get_aguardando_followup
from messages import msg_followup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def _membros_ativos() -> dict:
    if TEST_MODE:
        return {k: v for k, v in MEMBERS.items() if v["whatsapp"] == TEST_WHATSAPP}
    return MEMBERS


def job_kickoff():
    log.info("Disparando kickoff semanal (segunda 11h)...")
    for nome, dados in _membros_ativos().items():
        try:
            tarefas = get_tasks_socios(dados["lista_id"])
            enviar_mensagem(dados["whatsapp"], msg_kickoff(nome, tarefas))
            set_aguardando_prioridades(dados["whatsapp"])
            log.info(f"  Kickoff enviado para {nome}")
        except Exception as e:
            log.error(f"  Erro kickoff para {nome}: {e}")


def job_followup():
    log.info("Verificando follow-ups pendentes...")
    from config import WHATSAPP_TO_MEMBER
    aguardando = get_aguardando_followup()
    for wpp in aguardando:
        try:
            enviar_mensagem(wpp, msg_followup())
            log.info(f"  Follow-up enviado para {wpp}")
        except Exception as e:
            log.error(f"  Erro follow-up para {wpp}: {e}")


def job_daily():
    log.info("Disparando daily (08h30)...")
    for nome, dados in _membros_ativos().items():
        try:
            tarefas = get_tasks_socios(dados["lista_id"])
            enviar_mensagem(dados["whatsapp"], msg_daily(nome, tarefas))
            log.info(f"  Daily enviada para {nome}")
        except Exception as e:
            log.error(f"  Erro daily para {nome}: {e}")


def job_checkin():
    log.info("Disparando check-in (13h)...")
    for nome, dados in _membros_ativos().items():
        try:
            tarefas = get_tasks_socios(dados["lista_id"])
            if not tarefas["todas_pendentes"]:
                log.info(f"  {nome} sem pendências — checkin ignorado")
                continue
            enviar_mensagem(dados["whatsapp"], msg_checkin(nome, tarefas))
            log.info(f"  Checkin enviado para {nome}")
        except Exception as e:
            log.error(f"  Erro checkin para {nome}: {e}")


def job_pre_fechamento():
    log.info("Disparando pré-fechamento (17h30)...")
    for nome, dados in _membros_ativos().items():
        try:
            enviar_mensagem(dados["whatsapp"], msg_pre_fechamento(nome))
            log.info(f"  Pré-fechamento enviado para {nome}")
        except Exception as e:
            log.error(f"  Erro pré-fechamento para {nome}: {e}")


def job_fechamento():
    log.info("Disparando fechamento (18h)...")
    for nome, dados in _membros_ativos().items():
        try:
            tarefas = get_tasks_socios(dados["lista_id"])
            set_aguardando_fechamento(
                whatsapp=dados["whatsapp"],
                concluidas=[{"name": t["name"], "id": t["id"]} for t in tarefas["concluidas"]],
                nao_concluidas=[{"name": t["name"], "id": t["id"]} for t in tarefas["todas_pendentes"]],
            )
            enviar_mensagem(dados["whatsapp"], msg_fechamento(nome, tarefas))
            log.info(f"  Fechamento enviado para {nome}")
        except Exception as e:
            log.error(f"  Erro fechamento para {nome}: {e}")


def job_retrospectiva():
    log.info("Disparando retrospectiva (sexta 18h)...")
    for nome, dados in _membros_ativos().items():
        try:
            tarefas = get_tasks_socios(dados["lista_id"])
            set_aguardando_fechamento(
                whatsapp=dados["whatsapp"],
                concluidas=[{"name": t["name"], "id": t["id"]} for t in tarefas["concluidas"]],
                nao_concluidas=[{"name": t["name"], "id": t["id"]} for t in tarefas["todas_pendentes"]],
            )
            enviar_mensagem(dados["whatsapp"], msg_retrospectiva(nome, tarefas))
            log.info(f"  Retrospectiva enviada para {nome}")
        except Exception as e:
            log.error(f"  Erro retrospectiva para {nome}: {e}")


def job_wbr_prep():
    log.info("Disparando WBR prep (sexta 17h)...")
    for nome, dados in _membros_ativos().items():
        try:
            enviar_mensagem(dados["whatsapp"], msg_wbr_prep(nome))
            log.info(f"  WBR prep enviado para {nome}")
        except Exception as e:
            log.error(f"  Erro WBR prep para {nome}: {e}")


def iniciar():
    schedule.every().monday.at(HORARIO_KICKOFF).do(job_kickoff)

    schedule.every().tuesday.at(HORARIO_DAILY).do(job_daily)
    schedule.every().wednesday.at(HORARIO_DAILY).do(job_daily)
    schedule.every().thursday.at(HORARIO_DAILY).do(job_daily)
    schedule.every().friday.at(HORARIO_DAILY).do(job_daily)

    schedule.every().day.at(HORARIO_CHECKIN).do(job_checkin)
    schedule.every().day.at(HORARIO_PRE_FECHAMENTO).do(job_pre_fechamento)

    schedule.every().friday.at(HORARIO_WBR_PREP).do(job_wbr_prep)
    schedule.every().friday.at(HORARIO_RETROSPECTIVA).do(job_retrospectiva)

    schedule.every().monday.at(HORARIO_FECHAMENTO).do(job_fechamento)
    schedule.every().tuesday.at(HORARIO_FECHAMENTO).do(job_fechamento)
    schedule.every().wednesday.at(HORARIO_FECHAMENTO).do(job_fechamento)
    schedule.every().thursday.at(HORARIO_FECHAMENTO).do(job_fechamento)

    modo = "TESTE (só Victor)" if TEST_MODE else "PRODUÇÃO (todos)"
    log.info(f"Scheduler iniciado — modo {modo}")

    while True:
        schedule.run_pending()
        time.sleep(30)
