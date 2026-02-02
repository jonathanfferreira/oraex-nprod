"""
ORAEX - Dashboard Data Collector
--------------------------------
Script "Glue" para coletar dados de todos os componentes
e salvar nos arquivos JSON esperados pelo Dashboard.

Uso:
    python run_dashboard_data.py
    (Recomendado rodar via Crontab a cada 5-15 min)
"""
import os
import json
import logging
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Configuração de Caminhos
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
SCRIPTS_DIR = BASE_DIR / "automacao"

# Garante diretório de logs
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def run_script(script_path: Path, args: list, output_file: Path):
    """Roda um script e salva stdout no arquivo JSON."""
    logging.info(f"Executando {script_path.name}...")
    
    cmd = [sys.executable, str(script_path)] + args
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=300,
            cwd=str(BASE_DIR)
        )
        
        if result.returncode != 0 and result.returncode != 1: # 1 pode ser Warning
            logging.warning(f"Script {script_path.name} retornou código {result.returncode}")
            logging.warning(f"Stderr: {result.stderr}")
        
        # Tenta parsear JSON para validar
        try:
            data = json.loads(result.stdout)
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            logging.info(f"Dados salvos em {output_file.name}")
        except json.JSONDecodeError:
            logging.error(f"Saída inválida (não JSON) de {script_path.name}")
            logging.debug(f"Output raw: {result.stdout[:200]}")
            
    except Exception as e:
        logging.error(f"Falha ao executar {script_path.name}: {e}")

def main():
    logging.info("Iniciando coleta de dados para Dashboard...")
    
    # 1. Healthcheck
    run_script(
        SCRIPTS_DIR / "diagnosticos" / "oracle_healthcheck.py",
        ["--json", "--user", "system"], # Ajustar credenciais conforme env
        LOG_DIR / "healthcheck.json"
    )
    
    # 2. RMAN Status
    run_script(
        SCRIPTS_DIR / "backup" / "rman_backup_manager.py",
        ["--status", "--json", "--days", "7"],
        LOG_DIR / "rman_last.json"
    )
    
    # 3. ASM Capacity
    # ASM script writes to history file by itself if --history-file is passed,
    # but we want the report JSON for the dashboard.
    run_script(
        SCRIPTS_DIR / "monitoramento" / "asm_capacity_report.py",
        ["--json"],
        # Dashboard expects reports? No, dashboard API mocks ASM if invalid.
        # But wait, dashboard uses 'ASMCapacityStats' model.
        # Let's save the report.
        LOG_DIR / "asm_report.json" # Not directly used by dashboard yet, dashboard uses mocks or needs update
    )
    
    # Update Dashboard Logic:
    # Dashboard 'get_capacity' mocked read from JSON. 
    # Actually, let's fix the Dashboard API to read 'asm_report.json' too!
    
    logging.info("Coleta finalizada.")

if __name__ == "__main__":
    main()
