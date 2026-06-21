"""
Ponto de entrada. Em produção (Render) só roda o webhook/API.
O scheduler é gerenciado pelo GitHub Actions, que chama /internal/job/{nome}.
Para rodar localmente com scheduler integrado: python main_local.py
"""
import os
import uvicorn
import logging

from webhook import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
