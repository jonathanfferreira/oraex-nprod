"""
ORAEX - Prometheus Exporter
---------------------------
Exporta métricas do Oracle para formato Prometheus.
Pode rodar como servidor HTTP ou gerar arquivo de texto (Node Exporter).

Uso:
    python prometheus_exporter.py --port 9100  (Server mode)
    python prometheus_exporter.py --outfile /tmp/oraex.prom (Textfile mode)
"""
import argparse
import time
import sys
import logging
import random # Mock para demonstração se não tiver conexão
from datetime import datetime

# Tenta importar prometheus_client
try:
    from prometheus_client import start_http_server, Gauge, CollectorRegistry, write_to_textfile
    HAS_PROM = True
except ImportError:
    HAS_PROM = False

# Métricas
REGISTRY = CollectorRegistry() if HAS_PROM else None

# Definição de Gauges (Métricas)
if HAS_PROM:
    G_TABLESPACE_USED = Gauge('oraex_tablespace_used_pct', 'Tablespace usage %', ['tablespace'], registry=REGISTRY)
    G_ASM_FREE_GB = Gauge('oraex_asm_diskgroup_free_gb', 'ASM Diskgroup Free GB', ['diskgroup'], registry=REGISTRY)
    G_ASM_USED_PCT = Gauge('oraex_asm_diskgroup_used_pct', 'ASM Diskgroup Used %', ['diskgroup'], registry=REGISTRY)
    G_BACKUP_STATUS = Gauge('oraex_backup_last_status', 'Last Backup Status (1=Success, 0=Fail)', ['type'], registry=REGISTRY)
    G_ALERTS = Gauge('oraex_alerts_active', 'Active Critical Alerts', [], registry=REGISTRY)

def collect_metrics_mock():
    """Coleta métricas (Mock para demonstração)."""
    if not HAS_PROM:
        return

    # Mock Tablespaces
    G_TABLESPACE_USED.labels(tablespace='SYSTEM').set(random.uniform(40, 60))
    G_TABLESPACE_USED.labels(tablespace='SYSAUX').set(random.uniform(50, 70))
    G_TABLESPACE_USED.labels(tablespace='USERS').set(random.uniform(10, 80))
    G_TABLESPACE_USED.labels(tablespace='UNDOTBS1').set(random.uniform(1, 10))

    # Mock ASM
    G_ASM_FREE_GB.labels(diskgroup='DATA').set(548.5)
    G_ASM_USED_PCT.labels(diskgroup='DATA').set(73.2)
    G_ASM_FREE_GB.labels(diskgroup='FRA').set(224.0)
    G_ASM_USED_PCT.labels(diskgroup='FRA').set(78.1)

    # Mock Backup
    G_BACKUP_STATUS.labels(type='FULL').set(1)
    G_BACKUP_STATUS.labels(type='ARCH').set(1)

    # Mock Alerts
    G_ALERTS.set(0)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, help="Porta para servidor HTTP (ex: 9100)")
    parser.add_argument("--outfile", help="Arquivo de saída (.prom)")
    parser.add_argument("--interval", type=int, default=60, help="Intervalo de coleta (segundos)")
    args = parser.parse_args()

    setup_logging()

    if not HAS_PROM:
        logging.error("Biblioteca 'prometheus_client' não instalada. Instale com pip install prometheus-client")
        sys.exit(1)

    if args.port:
        logging.info(f"Iniciando servidor Prometheus na porta {args.port}...")
        start_http_server(args.port, registry=REGISTRY)
        while True:
            collect_metrics_mock()
            time.sleep(args.interval)
            
    elif args.outfile:
        logging.info(f"Escrevendo métricas em {args.outfile} (One-shot)...")
        collect_metrics_mock()
        write_to_textfile(args.outfile, registry=REGISTRY)
        logging.info("Feito.")
        
    else:
        logging.error("Especifique --port ou --outfile")
        sys.exit(1)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

if __name__ == "__main__":
    main()
