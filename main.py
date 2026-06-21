"""
Ponto de entrada. Roda o scheduler e o webhook em paralelo.
"""
import threading
import uvicorn
import logging

from scheduler import iniciar
from webhook import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def rodar_scheduler():
    log.info("Thread do scheduler iniciada.")
    iniciar()


def rodar_webhook():
    import os
    port = int(os.getenv("PORT", 8000))
    log.info(f"Thread do webhook iniciada na porta {port}.")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


if __name__ == "__main__":
    t_scheduler = threading.Thread(target=rodar_scheduler, daemon=True)
    t_scheduler.start()

    rodar_webhook()
