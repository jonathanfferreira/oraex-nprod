"""
ORAEX - Oracle Housekeeper
--------------------------
Remove Oracle Homes desativadas (detached) de forma segura.
Segue princípios DBRE: dry-run por padrão, verificação de processos.

Uso:
    python oracle_housekeeper.py --inventory /path/to/inventory.xml
    python oracle_housekeeper.py --force --confirm-delete  # Execução real
"""
import os
import sys
import argparse
import logging
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional


DEFAULT_INVENTORY = "/u01/app/oraInventory/ContentsXML/inventory.xml"


class OracleHome:
    """Representa uma Oracle Home do inventário."""
    def __init__(self, name: str, location: Path, is_removed: bool):
        self.name = name
        self.location = location
        self.is_removed = is_removed

    @property
    def exists(self) -> bool:
        return self.location.exists()

    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.location})"


class ProcessChecker:
    """Verifica processos ativos em uma Oracle Home."""

    @staticmethod
    def has_active_processes(home_path: Path) -> bool:
        """Retorna True se há processos rodando na home (PERIGO)."""
        try:
            cmd = f"ps -ef | grep '{home_path}' | grep -v grep"
            result = subprocess.run(
                cmd, shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                timeout=30
            )
            has_processes = result.returncode == 0 and bool(result.stdout.strip())
            if has_processes:
                logging.warning(f"Processos ATIVOS detectados em {home_path}")
            return has_processes
        except Exception as e:
            logging.error(f"Erro ao verificar processos: {e}")
            return True  # Fail-safe: assume que há processos


class InventoryParser:
    """Parse do arquivo inventory.xml."""

    @staticmethod
    def parse(inventory_path: Path) -> List[OracleHome]:
        """Lê inventory.xml e retorna lista de OracleHome."""
        if not inventory_path.exists():
            logging.error(f"Inventário não encontrado: {inventory_path}")
            return []

        try:
            tree = ET.parse(inventory_path)
            root = tree.getroot()
            
            homes = []
            for home in root.findall(".//HOME"):
                homes.append(OracleHome(
                    name=home.get("NAME", "unknown"),
                    location=Path(home.get("LOC", "")),
                    is_removed=home.get("REMOVED", "F") == "T"
                ))
            return homes
            
        except ET.ParseError as e:
            logging.error(f"Erro XML: {e}")
            return []


class OracleHousekeeper:
    """Gerencia limpeza de Oracle Homes desativadas."""

    def __init__(self, inventory_path: Path, dry_run: bool = True):
        self.inventory_path = inventory_path
        self.dry_run = dry_run
        self.homes: List[OracleHome] = []
        self.cleaned: List[str] = []
        self.skipped: List[str] = []

    def load_homes(self) -> None:
        """Carrega homes do inventário."""
        self.homes = InventoryParser.parse(self.inventory_path)
        logging.info(f"Total de Homes no inventário: {len(self.homes)}")

    def get_detached_homes(self) -> List[OracleHome]:
        """Retorna homes marcadas como REMOVED."""
        return [h for h in self.homes if h.is_removed]

    def cleanup_home(self, home: OracleHome) -> bool:
        """Remove uma home se seguro. Retorna True se removeu."""
        if not home.exists:
            logging.info(f"[SKIP] {home.display_name} - diretório não existe")
            self.skipped.append(home.name)
            return False

        if ProcessChecker.has_active_processes(home.location):
            logging.error(f"[ABORT] {home.display_name} - processos em execução!")
            self.skipped.append(home.name)
            return False

        if self.dry_run:
            logging.info(f"[DRY-RUN] Seria removido: {home.location}")
            return False

        try:
            logging.info(f"[DELETE] Removendo: {home.location}")
            shutil.rmtree(home.location)
            self.cleaned.append(home.name)
            logging.info(f"[OK] Removido com sucesso: {home.name}")
            return True
        except Exception as e:
            logging.error(f"[ERROR] Falha ao remover {home.name}: {e}")
            self.skipped.append(home.name)
            return False

    def run(self) -> dict:
        """Executa limpeza completa."""
        mode = "DRY-RUN" if self.dry_run else "DESTRUCTIVE"
        logging.info(f"Iniciando Housekeeper (Mode: {mode})")

        self.load_homes()
        detached = self.get_detached_homes()

        if not detached:
            logging.info("Nenhuma Home detached encontrada.")
            return {"total": 0, "cleaned": 0, "skipped": 0}

        logging.info(f"Encontradas {len(detached)} homes detached:")
        for home in detached:
            logging.info(f"  -> {home.display_name}")
            self.cleanup_home(home)

        return {
            "total": len(detached),
            "cleaned": len(self.cleaned),
            "skipped": len(self.skipped)
        }


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="ORAEX - Oracle Housekeeper"
    )
    parser.add_argument(
        "--inventory", 
        default=DEFAULT_INVENTORY,
        help="Caminho do inventory.xml"
    )
    parser.add_argument(
        "--force", 
        action="store_true",
        help="Executar remoção real (padrão: dry-run)"
    )
    parser.add_argument(
        "--confirm-delete", 
        action="store_true",
        help="Confirmação extra de segurança"
    )

    args = parser.parse_args()
    setup_logging()

    # Segurança: precisa de --force E --confirm-delete
    dry_run = True
    if args.force:
        if not args.confirm_delete:
            logging.error("Use --force --confirm-delete para execução real.")
            return 1
        dry_run = False

    housekeeper = OracleHousekeeper(
        inventory_path=Path(args.inventory),
        dry_run=dry_run
    )

    result = housekeeper.run()
    logging.info(f"Resumo: {result['cleaned']} removidas, {result['skipped']} ignoradas")

    return 0 if result["skipped"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
