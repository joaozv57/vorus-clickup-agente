import os
from dotenv import load_dotenv

load_dotenv()

# ClickUp
CLICKUP_TOKEN = os.getenv("CLICKUP_TOKEN", "pk_101222730_2IE2MQKTBOP1HCOQX2GXN0BYS0DS1FYC")
TEAM_ID = "90171198943"

# Listas
LIST_IDS = {
    "daily_sync":        "901714663218",
    "wbr_semanal":       "901714663219",
    "mbr_mensal":        "901714663220",
    "pos_encontro":      "901714663221",
    "pos_lancamento":    "901714663222",
    "pipeline":          "901714663212",
    "campanhas":         "901714663209",
    "projetos_ativos":   "901714663215",
}

# Membros
MEMBERS = {
    "Victor": {
        "clickup_id": "101222730",
        "whatsapp":   "5571993633174",
        "nome":       "Victor",
    },
    "Gabriel": {
        "clickup_id": "101222731",
        "whatsapp":   "5571992236378",
        "nome":       "Gabriel",
    },
    "Ton": {
        "clickup_id": "296568309",
        "whatsapp":   "5511937305357",
        "nome":       "Ton",
    },
}

# Mapa reverso: número WhatsApp → membro
WHATSAPP_TO_MEMBER = {v["whatsapp"]: k for k, v in MEMBERS.items()}

# Horários de disparo
HORARIO_MANHA        = "08:00"
HORARIO_TARDE        = "14:00"
HORARIO_PRE_FECHAMENTO = "17:30"
HORARIO_FECHAMENTO   = "18:00"
HORARIO_WBR_PREP     = "17:00"

# Z-API (plugar no final)
ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE", "")
ZAPI_TOKEN    = os.getenv("ZAPI_TOKEN", "")
ZAPI_BASE_URL = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}"

# Segurança dos endpoints internos (GitHub Actions → Render)
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "dev-secret-local")
