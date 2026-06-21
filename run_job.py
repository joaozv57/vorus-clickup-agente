"""
Chamado pelo GitHub Actions para disparar um job específico.
Uso: python run_job.py <nome-do-job>
"""
import sys
from scheduler import job_manha, job_tarde, job_pre_fechamento, job_fechamento, job_wbr_prep

JOBS = {
    "manha":          job_manha,
    "tarde":          job_tarde,
    "pre-fechamento": job_pre_fechamento,
    "fechamento":     job_fechamento,
    "wbr-prep":       job_wbr_prep,
}

if __name__ == "__main__":
    nome = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = JOBS.get(nome)
    if not fn:
        print(f"Job desconhecido: '{nome}'. Opções: {list(JOBS)}")
        sys.exit(1)
    fn()
