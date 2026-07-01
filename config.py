import os
from dotenv import load_dotenv

load_dotenv()

# ClickUp
CLICKUP_TOKEN = os.getenv("CLICKUP_TOKEN", "pk_101222730_2IE2MQKTBOP1HCOQX2GXN0BYS0DS1FYC")
TEAM_ID = "90171198943"

# ── Espaço Gestão Sócios (novo — não mexer nas listas antigas abaixo) ─────────
GESTAO_SOCIOS_SPACE_ID = "90176230211"

SOCIOS_LIST_IDS = {
    "ton":     "901714881107",   # [MARKETING] Ton Luccas
    "gabriel": "901714881108",   # [COMERCIAL] Gabriel Moreira
    "victor":  "901714881116",   # [AUTOMAÇÃO & DADOS] Victor Zolla
    "joao":    "901714881248",   # [OPERAÇÕES] João Ribeiro
}

SOCIOS_STATUSES = ["BACKLOG", "PLANNING", "EM ANDAMENTO", "BLOQUEADO", "CONCLUIDO"]

# ── Listas antigas (operação existente — NÃO MEXER) ───────────────────────────
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
        "lista_id":   SOCIOS_LIST_IDS["victor"],
    },
    "Gabriel": {
        "clickup_id": "101222731",
        "whatsapp":   "5571992236378",
        "nome":       "Gabriel",
        "lista_id":   SOCIOS_LIST_IDS["gabriel"],
    },
    "Ton": {
        "clickup_id": "296568309",
        "whatsapp":   "5511937305357",
        "nome":       "Ton",
        "lista_id":   SOCIOS_LIST_IDS["ton"],
    },
    "Joao": {
        "clickup_id": os.getenv("JOAO_CLICKUP_ID", ""),
        "whatsapp":   os.getenv("JOAO_WHATSAPP", ""),
        "nome":       "João",
        "lista_id":   SOCIOS_LIST_IDS["joao"],
    },
}

# Mapa reverso: número WhatsApp → membro
WHATSAPP_TO_MEMBER = {v["whatsapp"]: k for k, v in MEMBERS.items() if v["whatsapp"]}

# Horários de disparo
HORARIO_KICKOFF          = "08:00"   # Segunda
HORARIO_DAILY            = "08:30"   # Ter–Sex
HORARIO_CHECKIN          = "13:00"
HORARIO_PRE_FECHAMENTO   = "17:30"
HORARIO_FECHAMENTO       = "18:00"
HORARIO_RETROSPECTIVA    = "18:00"   # Sexta (substitui fechamento normal)

# Aliases de compatibilidade
HORARIO_MANHA            = HORARIO_DAILY
HORARIO_TARDE            = HORARIO_CHECKIN
HORARIO_WBR_PREP         = "17:00"

# Z-API
ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE", "")
ZAPI_TOKEN    = os.getenv("ZAPI_TOKEN", "")
ZAPI_BASE_URL = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}"

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Segurança dos endpoints internos
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "dev-secret-local")

# Modo de teste: mensagens vão apenas para o número abaixo
TEST_MODE     = os.getenv("TEST_MODE", "true").lower() == "true"
TEST_WHATSAPP = "5571993633174"  # Victor
