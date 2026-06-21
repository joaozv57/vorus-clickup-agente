import requests
from config import ZAPI_BASE_URL, ZAPI_INSTANCE, ZAPI_TOKEN


def _zapi_disponivel() -> bool:
    return bool(ZAPI_INSTANCE and ZAPI_TOKEN)


def enviar_mensagem(numero: str, texto: str) -> bool:
    """Envia mensagem de texto via Z-API. Retorna True se enviou."""
    if not _zapi_disponivel():
        # Modo de desenvolvimento: só printa no terminal
        print(f"\n[Z-API STUB] Para {numero}:\n{texto}\n{'─'*50}")
        return True

    try:
        r = requests.post(
            f"{ZAPI_BASE_URL}/send-text",
            json={"phone": numero, "message": texto},
            timeout=10,
        )
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[Z-API ERRO] Falha ao enviar para {numero}: {e}")
        return False


def enviar_para_todos(membros: dict, texto_fn) -> None:
    """Envia mensagem para todos os membros. texto_fn recebe o membro e retorna o texto."""
    for nome, dados in membros.items():
        texto = texto_fn(nome, dados)
        enviar_mensagem(dados["whatsapp"], texto)
