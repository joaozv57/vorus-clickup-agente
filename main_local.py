"""
Para testar localmente com scheduler integrado (sem GitHub Actions).
"""
import threading
import uvicorn
import logging

from scheduler import iniciar
from webhook import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == "__main__":
    t = threading.Thread(target=iniciar, daemon=True)
    t.start()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
