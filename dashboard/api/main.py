from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import json
import os
import platform
from pathlib import Path
from typing import List

# Import models
from .models import HealthCheckSummary, BackupJob, ASMCapacityStats, SystemStatus, DiskGroup

app = FastAPI(title="ORAEX Dashboard API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração de caminhos
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"  # Assumindo diretório de logs central
ASM_HISTORY = LOG_DIR / "asm_history.json"
LAST_BACKUP = LOG_DIR / "rman_last.json"
HEALTH_LOG = LOG_DIR / "healthcheck.json"

# Helper para ler JSON
def read_json_file(filepath: Path, default=None):
    if not filepath.exists():
        return default
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception:
        return default

@app.get("/api/health", response_model=SystemStatus)
def get_system_status():
    return SystemStatus(
        hostname=platform.node(),
        platform=platform.system()
    )

@app.get("/api/checks", response_model=HealthCheckSummary)
def get_health_checks():
    # Mock por enquanto, idealmente o healthcheck.py salvaria um JSON
    return HealthCheckSummary(
        total=5,
        ok=4,
        warnings=1,
        critical=0,
        errors=0,
        status="WARNING"
    )

@app.get("/api/backups", response_model=List[BackupJob])
def get_backups():
    # Tenta ler do arquivo, senão retorna mock
    data = read_json_file(LAST_BACKUP)
    if data:
        return [BackupJob(**job) for job in data]
    
    # Mock data
    return [
        BackupJob(
            session_key=101,
            start_time="2026-02-01T22:00:00",
            end_time="2026-02-01T23:00:00",
            status="COMPLETED",
            input_type="DB FULL",
            output_gb=50.5,
            elapsed_minutes=60
        ),
        BackupJob(
            session_key=102,
            start_time="2026-02-02T10:00:00",
            end_time="2026-02-02T10:05:00",
            status="COMPLETED",
            input_type="ARCHIVELOG",
            output_gb=1.2,
            elapsed_minutes=5
        )
    ]

@app.get("/api/capacity", response_model=ASMCapacityStats)
def get_capacity():
    # Tenta ler do report real
    ASM_REPORT = LOG_DIR / "asm_report.json"
    data = read_json_file(ASM_REPORT)
    
    if data:
        # Mapeia do formato do report para o modelo da API
        # O report tem 'diskgroups' (lista de dicts) e 'alerts' (lista de dicts)
        # O modelo DiskGroup na API espera chaves específicas.
        return ASMCapacityStats(
            diskgroups=[DiskGroup(**dg) for dg in data.get("diskgroups", [])],
            alerts=data.get("alerts", [])
        )

    # Fallback / Mock
    return ASMCapacityStats(
        diskgroups=[
            DiskGroup(name="DATA", state="MOUNTED", total_gb=2048, used_gb=1500, free_gb=548, used_pct=73.2),
            DiskGroup(name="REDO", state="MOUNTED", total_gb=100, used_gb=20, free_gb=80, used_pct=20.0),
            DiskGroup(name="FRA", state="MOUNTED", total_gb=1024, used_gb=800, free_gb=224, used_pct=78.1),
        ],
        alerts=[
            {"level": "WARNING", "group": "FRA", "message": "FRA acima de 75% (Mock)"}
        ]
    )

# Servir arquivos estáticos (Frontend)
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")

if __name__ == "__main__":
    uvicorn.run("dashboard.api.main:app", host="0.0.0.0", port=8000, reload=True)
