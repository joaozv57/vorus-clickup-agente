import os
import requests
from config import ZAPI_BASE_URL, ZAPI_INSTANCE, ZAPI_TOKEN


def _zapi_disponivel() -> bool:
    return bool(ZAPI_INSTANCE and ZAPI_TOKEN)


def enviar_mensagem(numero: str, texto: str) -> bool:
    if not _zapi_disponivel():
        print(f"\n[Z-API STUB] Para {numero}:\n{texto}\n{'─'*50}")
        return True

    try:
        headers = {"Content-Type": "application/json"}
        client_token = os.getenv("ZAPI_CLIENT_TOKEN", "")
        if client_token:
            headers["Client-Token"] = client_token

        r = requests.post(
            f"{ZAPI_BASE_URL}/send-text",
            headers=headers,
            json={"phone": numero, "message": texto},
            timeout=15,
        )
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[Z-API ERRO] Falha ao enviar para {numero}: {e}")
        return False


def enviar_para_todos(membros: dict, texto_fn) -> None:
    for nome, dados in membros.items():
        texto = texto_fn(nome, dados)
        enviar_mensagem(dados["whatsapp"], texto)
