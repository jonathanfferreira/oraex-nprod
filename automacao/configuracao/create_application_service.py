#!/usr/bin/env python3
"""
CREATE_APPLICATION_SERVICE.PY - Padronização de Services Oracle (Item 6 Book DBA)
Nomenclatura: [APP_NAME]SRV[SITE] (Ex: INTEGSRVPRD)
"""

import os
import sys
import argparse
import logging
import subprocess
import re
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

VALID_SITES = {"PRD": "Produção", "HG": "Homologação", "DEV": "Desenvolvimento", "QA": "QA", "DR": "DR"}

class OracleServiceManager:
    def __init__(self, db_name: str, oracle_home: str = None):
        self.db_name = db_name.upper()
        self.oracle_home = oracle_home or os.environ.get("ORACLE_HOME", "")
    
    def _run_srvctl(self, args: List[str]) -> Tuple[int, str, str]:
        srvctl_path = os.path.join(self.oracle_home, "bin", "srvctl") if self.oracle_home else "srvctl"
        try:
            result = subprocess.run([srvctl_path] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            return result.returncode, result.stdout.decode('utf-8'), result.stderr.decode('utf-8')
        except Exception as e:
            return -1, "", str(e)
    
    def list_services(self) -> List[Dict]:
        rc, stdout, _ = self._run_srvctl(["status", "service", "-d", self.db_name])
        services = []
        for line in stdout.splitlines():
            match = re.match(r"Service\s+(\w+)\s+is\s+(\w+)", line.strip())
            if match:
                services.append({"name": match.group(1), "status": match.group(2)})
        return services
    
    def service_exists(self, name: str) -> bool:
        rc, _, _ = self._run_srvctl(["config", "service", "-d", self.db_name, "-s", name])
        return rc == 0
    
    def create_service(self, name: str, preferred: List[str] = None, dry_run: bool = True) -> bool:
        if self.service_exists(name):
            logging.warning(f"Service {name} já existe!")
            return False
        cmd = ["add", "service", "-d", self.db_name, "-s", name, "-e", "SELECT", "-m", "BASIC"]
        if preferred:
            cmd.extend(["-r", ",".join(preferred)])
        if dry_run:
            logging.info(f"[DRY-RUN] srvctl {' '.join(cmd)}")
            return True
        rc, _, stderr = self._run_srvctl(cmd)
        if rc != 0:
            logging.error(f"Erro: {stderr}")
            return False
        logging.info(f"Service {name} criado!")
        return True
    
    def start_service(self, name: str, dry_run: bool = True) -> bool:
        if dry_run:
            logging.info(f"[DRY-RUN] Iniciaria: {name}")
            return True
        rc, _, stderr = self._run_srvctl(["start", "service", "-d", self.db_name, "-s", name])
        return rc == 0

def generate_service_name(app: str, site: str) -> str:
    return f"{re.sub(r'[^A-Z0-9]', '', app.upper())}SRV{site.upper()}"

def main():
    parser = argparse.ArgumentParser(description="Gerenciador de Services Oracle")
    parser.add_argument("--db", required=True, help="Nome do banco")
    parser.add_argument("--app", required=True, help="Nome da aplicação")
    parser.add_argument("--site", required=True, choices=VALID_SITES.keys(), help="Site")
    parser.add_argument("--apply", action="store_true", help="Executar (padrão dry-run)")
    parser.add_argument("--start", action="store_true", help="Iniciar após criar")
    args = parser.parse_args()
    
    manager = OracleServiceManager(args.db)
    service_name = generate_service_name(args.app, args.site)
    
    print(f"\n📋 Service: {service_name} ({args.app} @ {args.site})")
    
    if manager.create_service(service_name, dry_run=not args.apply):
        if args.apply and args.start:
            manager.start_service(service_name, dry_run=False)

if __name__ == "__main__":
    main()
