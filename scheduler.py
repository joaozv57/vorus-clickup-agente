import schedule
import time
import logging
from config import MEMBERS, HORARIO_MANHA, HORARIO_TARDE, HORARIO_PRE_FECHAMENTO, HORARIO_FECHAMENTO, HORARIO_WBR_PREP
from clickup import get_tasks_hoje
from messages import msg_manha, msg_tarde, msg_pre_fechamento, msg_wbr_prep, msg_fechamento
from zapi import enviar_mensagem
from state import set_aguardando_fechamento

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def job_manha():
    log.info("Disparando agenda da manhã...")
    for nome, dados in MEMBERS.items():
        try:
            tarefas = get_tasks_hoje(dados["clickup_id"])
            texto = msg_manha(nome, tarefas)
            enviar_mensagem(dados["whatsapp"], texto)
            log.info(f"  Manhã enviada para {nome}")
        except Exception as e:
            log.error(f"  Erro ao enviar manhã para {nome}: {e}")


def job_tarde():
    log.info("Disparando cobrança da tarde...")
    for nome, dados in MEMBERS.items():
        try:
            tarefas = get_tasks_hoje(dados["clickup_id"])
            pendentes = tarefas.get("todas_pendentes", [])
            if not pendentes:
                log.info(f"  {nome} sem pendências — não enviando tarde")
                continue
            texto = msg_tarde(nome, tarefas)
            enviar_mensagem(dados["whatsapp"], texto)
            log.info(f"  Tarde enviada para {nome}")
        except Exception as e:
            log.error(f"  Erro ao enviar tarde para {nome}: {e}")


def job_fechamento():
    log.info("Disparando fechamento do dia...")
    for nome, dados in MEMBERS.items():
        try:
            tarefas = get_tasks_hoje(dados["clickup_id"])
            concluidas = tarefas.get("concluidas", [])
            nao_concluidas = tarefas.get("todas_pendentes", [])

            # Salva estado: aguardando resposta do WhatsApp
            set_aguardando_fechamento(
                whatsapp=dados["whatsapp"],
                concluidas=[{"name": t["name"], "id": t["id"]} for t in concluidas],
                nao_concluidas=[{"name": t["name"], "id": t["id"]} for t in nao_concluidas],
            )

            texto = msg_fechamento(nome, tarefas)
            enviar_mensagem(dados["whatsapp"], texto)
            log.info(f"  Fechamento enviado para {nome}")
        except Exception as e:
            log.error(f"  Erro ao enviar fechamento para {nome}: {e}")


def job_pre_fechamento():
    log.info("Disparando aviso de pré-fechamento (17:30)...")
    for nome, dados in MEMBERS.items():
        try:
            texto = msg_pre_fechamento(nome)
            enviar_mensagem(dados["whatsapp"], texto)
            log.info(f"  Pré-fechamento enviado para {nome}")
        except Exception as e:
            log.error(f"  Erro ao enviar pré-fechamento para {nome}: {e}")


def job_wbr_prep():
    log.info("Disparando aviso de prep WBR (sexta 17:00)...")
    for nome, dados in MEMBERS.items():
        try:
            texto = msg_wbr_prep(nome)
            enviar_mensagem(dados["whatsapp"], texto)
            log.info(f"  WBR prep enviado para {nome}")
        except Exception as e:
            log.error(f"  Erro ao enviar WBR prep para {nome}: {e}")


def iniciar():
    schedule.every().day.at(HORARIO_MANHA).do(job_manha)
    schedule.every().day.at(HORARIO_TARDE).do(job_tarde)
    schedule.every().day.at(HORARIO_PRE_FECHAMENTO).do(job_pre_fechamento)
    schedule.every().day.at(HORARIO_FECHAMENTO).do(job_fechamento)
    schedule.every().friday.at(HORARIO_WBR_PREP).do(job_wbr_prep)

    log.info(
        f"Scheduler iniciado. Horários: {HORARIO_MANHA} | {HORARIO_TARDE} | "
        f"{HORARIO_PRE_FECHAMENTO} (pré-fechamento) | {HORARIO_FECHAMENTO} | "
        f"{HORARIO_WBR_PREP} (sextas, WBR prep)"
    )

    while True:
        schedule.run_pending()
        time.sleep(30)
