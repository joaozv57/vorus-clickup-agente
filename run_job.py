"""
Utilitário local para disparar um job manualmente sem passar pelo Render.
Uso: python run_job.py <nome-do-job>

Para produção, o GitHub Actions chama /internal/job/<nome> no Render.
"""
import sys
from scheduler import (
    job_kickoff, job_daily, job_checkin,
    job_pre_fechamento, job_fechamento,
    job_retrospectiva, job_wbr_prep, job_followup,
)

JOBS = {
    "kickoff":        job_kickoff,
    "daily":          job_daily,
    "checkin":        job_checkin,
    "pre-fechamento": job_pre_fechamento,
    "fechamento":     job_fechamento,
    "retrospectiva":  job_retrospectiva,
    "wbr-prep":       job_wbr_prep,
    "followup":       job_followup,
}

if __name__ == "__main__":
    nome = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = JOBS.get(nome)
    if not fn:
        print(f"Job desconhecido: '{nome}'. Opcoes: {list(JOBS)}")
        sys.exit(1)
    fn()
