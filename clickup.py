import requests
from datetime import datetime, date, timedelta, timezone
from config import CLICKUP_TOKEN, LIST_IDS, SOCIOS_LIST_IDS
from categorias import prefixar

BASE = "https://api.clickup.com/api/v2"
HEADERS = {"Authorization": CLICKUP_TOKEN, "Content-Type": "application/json"}


def _status_por_data(due_date_ms: int = None) -> str:
    """
    PLANNING = semana corrente (seg–dom).
    BACKLOG  = sem data ou data em semana futura.
    """
    if not due_date_ms:
        return "backlog(no radar)"
    hoje = date.today()
    inicio_semana = hoje - timedelta(days=hoje.weekday())   # segunda-feira
    fim_semana    = inicio_semana + timedelta(days=6)       # domingo
    due = date.fromtimestamp(due_date_ms / 1000)
    return "planning(essa semana)" if inicio_semana <= due <= fim_semana else "backlog(no radar)"


def _get(path, params=None):
    r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()


def _post(path, data):
    r = requests.post(f"{BASE}{path}", headers=HEADERS, json=data)
    r.raise_for_status()
    return r.json()


def get_tasks_socios(lista_id: str) -> dict:
    """Retorna tarefas da lista pessoal do sócio em Gestão Sócios."""
    try:
        resp = _get(f"/list/{lista_id}/task", {"include_closed": "false"})
        todas = resp.get("tasks", [])
    except Exception:
        todas = []

    def s(t):
        return t["status"]["status"].lower()

    concluidas   = [t for t in todas if s(t) in ("concluido", "concluído", "complete", "done")]
    pendentes    = [t for t in todas if s(t) not in ("concluido", "concluído", "complete", "done")]
    bloqueadas   = [t for t in pendentes if s(t) == "bloqueado"]
    em_andamento = [t for t in pendentes if s(t) == "em andamento(hoje)"]
    planning     = [t for t in pendentes if s(t) == "planning(essa semana)"]
    backlog      = [t for t in pendentes if s(t) == "backlog(no radar)"]

    return {
        "concluidas":      concluidas,
        "em_andamento":    em_andamento,
        "planning":        planning,
        "backlog":         backlog,
        "bloqueadas":      bloqueadas,
        "todas_pendentes": pendentes,
    }


def criar_tarefa_socios(lista_id: str, nome: str, assignee_id: str, due_date: int = None) -> dict:
    """PLANNING se a data cair na semana corrente; BACKLOG caso contrário ou sem data."""
    payload = {
        "name": prefixar(nome),
        "assignees": [int(assignee_id)] if assignee_id else [],
        "status": _status_por_data(due_date),
    }
    if due_date:
        payload["due_date"] = due_date
        payload["due_date_time"] = True
    return _post(f"/list/{lista_id}/task", payload)


def criar_multiplas_tarefas(lista_id: str, tarefas: list, assignee_id: str) -> list:
    """Cria várias tarefas de uma vez. tarefas = [{nome, prazo}]"""
    criadas = []
    for t in tarefas:
        try:
            due = t.get("due_date") or t.get("prazo_ts")
            start = t.get("start_date") or t.get("start_ts")
            payload = {
                "name": prefixar(t.get("nome", t.get("name", ""))),
                "assignees": [int(assignee_id)] if assignee_id else [],
                "status": _status_por_data(due),
            }
            if due:
                payload["due_date"] = due
                payload["due_date_time"] = True
            if start:
                payload["start_date"] = start
                payload["start_date_time"] = True
            r = _post(f"/list/{lista_id}/task", payload)
            criadas.append(r)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erro ao criar tarefa '{t}': {e}")
    return criadas


def get_tasks_hoje(member_clickup_id: str) -> dict:
    hoje_ts = int(datetime.combine(date.today(), datetime.min.time()).timestamp() * 1000)
    amanha_ts = hoje_ts + 86400000
    params = {
        "assignees[]": member_clickup_id,
        "due_date_gt": hoje_ts - 1,
        "due_date_lt": amanha_ts,
        "include_closed": "true",
    }
    todas = []
    for list_id in LIST_IDS.values():
        try:
            resp = _get(f"/list/{list_id}/task", params)
            todas.extend(resp.get("tasks", []))
        except Exception:
            pass

    concluidas   = [t for t in todas if t["status"]["status"].lower() in ("concluido", "concluído", "done", "complete")]
    pendentes    = [t for t in todas if t["status"]["status"].lower() not in ("concluido", "concluído", "done", "complete")]
    bloqueadas   = [t for t in pendentes if t["status"]["status"].lower() == "bloqueado"]
    em_andamento = [t for t in pendentes if t["status"]["status"].lower() == "em andamento(hoje)"]
    a_fazer      = [t for t in pendentes if t["status"]["status"].lower() == "a fazer"]

    return {
        "concluidas":      concluidas,
        "em_andamento":    em_andamento,
        "bloqueadas":      bloqueadas,
        "a_fazer":         a_fazer,
        "todas_pendentes": pendentes,
    }


def get_todas_tarefas_membro(member_clickup_id: str) -> list:
    params = {"assignees[]": member_clickup_id, "include_closed": "false"}
    todas = []
    for list_id in LIST_IDS.values():
        try:
            resp = _get(f"/list/{list_id}/task", params)
            todas.extend(resp.get("tasks", []))
        except Exception:
            pass
    return todas


def criar_relatorio_daily(nome: str, concluidas: list, nao_concluidas: list, resposta_wpp: str) -> dict:
    hoje = date.today().strftime("%d/%m/%Y")
    linhas_feitas    = "\n".join([f"  ✓ {t['name']}" for t in concluidas]) or "  Nenhuma"
    linhas_nao_feitas = "\n".join([f"  ✗ {t['name']}" for t in nao_concluidas]) or "  Nenhuma"
    descricao = (
        f"Daily — {nome} — {hoje}\n\n"
        f"O QUE FEZ HOJE:\n{linhas_feitas}\n\n"
        f"O QUE NÃO CONCLUIU:\n{linhas_nao_feitas}\n\n"
        f"MOTIVO / BLOQUEIO E PLANO DE AMANHÃ:\n  {resposta_wpp}\n"
    )
    return _post(f"/list/{LIST_IDS['daily_sync']}/task", {
        "name": f"Daily {nome} — {hoje}",
        "description": descricao,
        "status": "Concluido",
    })


def criar_tarefa(list_id: str, nome: str, descricao: str, assignee_id: str, due_date: int = None, start_date: int = None) -> dict:
    data = {"name": prefixar(nome), "description": descricao, "assignees": [int(assignee_id)], "status": _status_por_data(due_date)}
    if due_date:
        data["due_date"] = due_date
        data["due_date_time"] = True
    if start_date:
        data["start_date"] = start_date
        data["start_date_time"] = True
    return _post(f"/list/{list_id}/task", data)


def atualizar_status_tarefa(task_id: str, status: str) -> dict:
    r = requests.put(f"{BASE}/task/{task_id}", headers=HEADERS, json={"status": status})
    r.raise_for_status()
    return r.json()


_BRT = timezone(timedelta(hours=-3))
_DIAS_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


def mover_semana_para_planning(lista_id: str) -> int:
    """Segunda-feira: move tarefas BACKLOG da semana corrente para PLANNING."""
    hoje   = date.today()
    seg    = hoje - timedelta(days=hoje.weekday())
    sex    = seg + timedelta(days=4)
    todas  = _get(f"/list/{lista_id}/task", {"include_closed": False}).get("tasks", [])
    movidas = 0
    for t in todas:
        if t["status"]["status"].lower() != "backlog(no radar)":
            continue
        due_raw = t.get("due_date")
        if not due_raw:
            continue
        due_date = datetime.fromtimestamp(int(due_raw) / 1000, tz=_BRT).date()
        if seg <= due_date <= sex:
            atualizar_status_tarefa(t["id"], "planning(essa semana)")
            movidas += 1
    return movidas


def mover_dia_para_andamento(lista_id: str) -> int:
    """Diariamente: move tarefas PLANNING de hoje para EM ANDAMENTO."""
    hoje    = date.today()
    todas   = _get(f"/list/{lista_id}/task", {"include_closed": False}).get("tasks", [])
    movidas = 0
    for t in todas:
        if t["status"]["status"].lower() != "planning(essa semana)":
            continue
        due_raw = t.get("due_date")
        if not due_raw:
            continue
        due_date = datetime.fromtimestamp(int(due_raw) / 1000, tz=_BRT).date()
        if due_date == hoje:
            atualizar_status_tarefa(t["id"], "em andamento(hoje)")
            movidas += 1
    return movidas


def get_tasks_dia(lista_id: str, dia: date = None) -> list:
    """
    Retorna tarefas de um dia específico ordenadas por start_date.
    Cada item: {id, name, start_dt, due_dt, bullets, status}
    """
    if dia is None:
        dia = date.today()

    todas = _get(f"/list/{lista_id}/task", {"include_closed": False}).get("tasks", [])
    resultado = []
    for t in todas:
        due_raw = t.get("due_date")
        if not due_raw:
            continue
        due_dt = datetime.fromtimestamp(int(due_raw) / 1000, tz=_BRT)
        if due_dt.date() != dia:
            continue
        start_raw = t.get("start_date")
        start_dt = datetime.fromtimestamp(int(start_raw) / 1000, tz=_BRT) if start_raw else due_dt

        desc = (t.get("description") or "").strip()
        bullets = [
            linha.strip().lstrip("-·• ").strip()
            for linha in desc.split("\n")
            if linha.strip().lstrip("-·• ").strip()
        ]

        resultado.append({
            "id":       t["id"],
            "name":     t["name"],
            "start_dt": start_dt,
            "due_dt":   due_dt,
            "bullets":  bullets,
            "status":   t["status"]["status"].lower(),
        })

    resultado.sort(key=lambda x: x["start_dt"])
    return resultado


def encontrar_slots_livres(lista_id: str, duracao_min: int, janelas_bloqueadas: dict = None, dias_frente: int = 7) -> list:
    """
    Encontra até 3 slots livres nos próximos dias respeitando janelas bloqueadas do membro
    e tarefas já agendadas. Retorna lista de {data, inicio, fim, start_ts, due_ts}.
    janelas_bloqueadas: dict do perfil do membro (weekday → [(h_i, m_i, h_f, m_f)]).
    """
    from config import HORARIO_TRABALHO_INICIO, HORARIO_TRABALHO_FIM

    bloqueios = janelas_bloqueadas or {}
    hoje      = date.today()
    dia_ini   = HORARIO_TRABALHO_INICIO[0] * 60 + HORARIO_TRABALHO_INICIO[1]
    dia_fim   = HORARIO_TRABALHO_FIM[0]    * 60 + HORARIO_TRABALHO_FIM[1]
    sugestoes = []

    for delta in range(1, dias_frente + 1):
        dia = hoje + timedelta(days=delta)
        if dia.weekday() >= 5:
            continue

        tarefas = get_tasks_dia(lista_id, dia)

        # Intervalos ocupados em minutos desde meia-noite
        ocupados = []
        for h_i, m_i, h_f, m_f in bloqueios.get(dia.weekday(), []):
            ocupados.append((h_i * 60 + m_i, h_f * 60 + m_f))
        for t in tarefas:
            s, e = t["start_dt"], t["due_dt"]
            ocupados.append((s.hour * 60 + s.minute, e.hour * 60 + e.minute))

        # Mesclar intervalos sobrepostos
        ocupados.sort()
        merged = []
        for ini, fim in ocupados:
            if merged and ini <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], fim)
            else:
                merged.append([ini, fim])

        def _arredondar_hora(minutos: int) -> int:
            """Arredonda para a próxima hora cheia."""
            h = minutos // 60
            return (h + 1) * 60 if minutos % 60 != 0 else minutos

        # Primeiro slot livre >= duracao_min (sempre em hora cheia)
        cursor = _arredondar_hora(dia_ini)
        slot = None
        for ini_ocup, fim_ocup in merged:
            if cursor + duracao_min <= ini_ocup:
                slot = cursor
                break
            cursor = _arredondar_hora(max(cursor, fim_ocup))
        if slot is None and cursor + duracao_min <= dia_fim:
            slot = cursor

        if slot is not None:
            h_i, m_i = divmod(slot, 60)
            h_f, m_f = divmod(slot + duracao_min, 60)
            ini_str = f"{h_i:02d}:{m_i:02d}"
            fim_str = f"{h_f:02d}:{m_f:02d}"
            sugestoes.append({
                "data":     dia,
                "inicio":   ini_str,
                "fim":      fim_str,
                "start_ts": int(datetime.strptime(f"{dia} {ini_str}", "%Y-%m-%d %H:%M")
                                .replace(tzinfo=_BRT).timestamp() * 1000),
                "due_ts":   int(datetime.strptime(f"{dia} {fim_str}", "%Y-%m-%d %H:%M")
                                .replace(tzinfo=_BRT).timestamp() * 1000),
            })

        if len(sugestoes) >= 3:
            break

    return sugestoes


def reagendar_tarefa(task_id: str, start_ts: int, due_ts: int) -> dict:
    """Atualiza datas de uma tarefa e ajusta status por data."""
    r = requests.put(f"{BASE}/task/{task_id}", headers=HEADERS, json={
        "start_date":      start_ts,
        "start_date_time": True,
        "due_date":        due_ts,
        "due_date_time":   True,
        "status":          _status_por_data(due_ts),
    })
    r.raise_for_status()
    return r.json()


def cancelar_tarefa(task_id: str) -> dict:
    """Remove a data da tarefa e move para BACKLOG."""
    r = requests.put(f"{BASE}/task/{task_id}", headers=HEADERS, json={"status": "backlog(no radar)"})
    r.raise_for_status()
    return r.json()


def buscar_tarefa_por_nome(lista_id: str, nome_parcial: str) -> dict | None:
    """Busca a tarefa mais próxima pelo nome (case-insensitive, sem prefixo de categoria)."""
    tarefas = _get(f"/list/{lista_id}/task", {"include_closed": False}).get("tasks", [])
    nome_lower = nome_parcial.lower()
    for t in tarefas:
        # compara sem prefixo de categoria
        name = t["name"]
        for p in ["[OPERACIONAL] ", "[TÁTICO] ", "[ESTRATÉGICO] "]:
            if name.startswith(p):
                name = name[len(p):]
                break
        if nome_lower in name.lower():
            return t
    return None
