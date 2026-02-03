"""
Self-Healing Runner
-------------------
Executa todos os runbooks de auto-remediação em sequência.
Pode ser agendado via cron para verificações periódicas.

Uso:
    python -m automacao.runbooks.runner --all
    python -m automacao.runbooks.runner --runbook tablespace
    python -m automacao.runbooks.runner --dry-run
"""
import logging
import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Optional

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from automacao.utils.connection import ConnectionConfig
    from automacao.utils.alerting import AlertManager, send_alert
except ImportError:
    ConnectionConfig = None
    AlertManager = None
    def send_alert(severity, message, details=None):
        logging.info(f"[{severity}] {message}")


class RunbookRunner:
    """Orquestrador de execução de runbooks."""
    
    AVAILABLE_RUNBOOKS = {
        "tablespace": "automacao.runbooks.tablespace_auto_resize.TablespaceAutoResize",
        "listener": "automacao.runbooks.listener_auto_restart.ListenerAutoRestart",
        "archive": "automacao.runbooks.archive_cleanup.ArchiveLogCleanup",
    }
    
    def __init__(
        self,
        config: Optional["ConnectionConfig"] = None,
        oracle_home: str = "/u01/app/oracle/product/19.0.0/dbhome_1",
        dry_run: bool = False
    ):
        self.config = config
        self.oracle_home = oracle_home
        self.dry_run = dry_run
        self.results: List[Dict] = []
        self.logger = logging.getLogger("RunbookRunner")
    
    def run_all(self) -> Dict:
        """Executa todos os runbooks disponíveis."""
        self.logger.info("=" * 60)
        self.logger.info("INICIANDO EXECUÇÃO DE TODOS OS RUNBOOKS")
        self.logger.info(f"Timestamp: {datetime.now().isoformat()}")
        self.logger.info(f"Dry-run: {self.dry_run}")
        self.logger.info("=" * 60)
        
        for name in self.AVAILABLE_RUNBOOKS:
            self.run_single(name)
        
        return self._generate_report()
    
    def run_single(self, runbook_name: str) -> Dict:
        """Executa um runbook específico."""
        if runbook_name not in self.AVAILABLE_RUNBOOKS:
            return {"error": f"Runbook '{runbook_name}' não encontrado"}
        
        self.logger.info(f"\n--- Executando: {runbook_name} ---")
        
        try:
            # Import dinâmico
            module_path = self.AVAILABLE_RUNBOOKS[runbook_name]
            module_name, class_name = module_path.rsplit(".", 1)
            
            module = __import__(module_name, fromlist=[class_name])
            runbook_class = getattr(module, class_name)
            
            # Instanciar baseado no tipo
            if runbook_name == "tablespace":
                runbook = runbook_class(
                    config=self.config,
                    dry_run=self.dry_run
                )
            elif runbook_name == "listener":
                runbook = runbook_class(
                    oracle_home=self.oracle_home,
                    dry_run=self.dry_run
                )
            elif runbook_name == "archive":
                runbook = runbook_class(
                    config=self.config,
                    oracle_home=self.oracle_home,
                    dry_run=self.dry_run
                )
            else:
                runbook = runbook_class(dry_run=self.dry_run)
            
            # Executar
            result = runbook.run()
            result["runbook"] = runbook_name
            result["timestamp"] = datetime.now().isoformat()
            
            self.results.append(result)
            
            # Log resultado
            status_emoji = "✅" if result["success"] else "❌"
            self.logger.info(f"{status_emoji} {runbook_name}: {result['status']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao executar {runbook_name}: {e}")
            result = {
                "runbook": runbook_name,
                "status": "ERROR",
                "success": False,
                "errors": [str(e)],
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(result)
            return result
    
    def _generate_report(self) -> Dict:
        """Gera relatório consolidado."""
        total = len(self.results)
        success = sum(1 for r in self.results if r.get("success"))
        failed = total - success
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "summary": {
                "total": total,
                "success": success,
                "failed": failed
            },
            "results": self.results
        }
        
        # Log summary
        self.logger.info("\n" + "=" * 60)
        self.logger.info("RELATÓRIO CONSOLIDADO")
        self.logger.info(f"Total: {total} | Sucesso: {success} | Falhas: {failed}")
        self.logger.info("=" * 60)
        
        # Alertar se houver falhas
        if failed > 0:
            send_alert(
                "WARNING",
                f"Self-healing: {failed}/{total} runbooks falharam",
                {"failed_runbooks": [r["runbook"] for r in self.results if not r.get("success")]}
            )
        else:
            send_alert(
                "OK",
                f"Self-healing: {total} runbooks executados com sucesso",
                {"dry_run": self.dry_run}
            )
        
        return report


def main():
    """Entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Self-Healing Runbook Runner")
    parser.add_argument("--all", action="store_true", help="Executar todos os runbooks")
    parser.add_argument("--runbook", help="Executar runbook específico (tablespace, listener, archive)")
    parser.add_argument("--dsn", help="DSN Oracle")
    parser.add_argument("--user", help="User Oracle")
    parser.add_argument("--password", help="Password Oracle")
    parser.add_argument("--oracle-home", default="/u01/app/oracle/product/19.0.0/dbhome_1")
    parser.add_argument("--dry-run", action="store_true", help="Apenas detecta, não corrige")
    parser.add_argument("--json", action="store_true", help="Output em JSON")
    parser.add_argument("--list", action="store_true", help="Listar runbooks disponíveis")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    if args.list:
        print("\nRunbooks disponíveis:")
        for name, path in RunbookRunner.AVAILABLE_RUNBOOKS.items():
            print(f"  - {name}: {path}")
        return 0
    
    # Configurar conexão
    if ConnectionConfig:
        config = ConnectionConfig.from_cli(args.dsn, args.user, args.password)
    else:
        from collections import namedtuple
        Config = namedtuple('Config', ['dsn', 'username', 'password'])
        config = Config(
            args.dsn or os.environ.get("ORACLE_DSN", "localhost/orcl"),
            args.user or os.environ.get("ORACLE_USER", "system"),
            args.password or os.environ.get("ORACLE_PASSWORD", "oracle")
        )
    
    runner = RunbookRunner(
        config=config,
        oracle_home=args.oracle_home,
        dry_run=args.dry_run
    )
    
    if args.all:
        report = runner.run_all()
    elif args.runbook:
        report = runner.run_single(args.runbook)
    else:
        parser.print_help()
        return 1
    
    if args.json:
        print(json.dumps(report, indent=2))
    
    # Exit code baseado em sucesso
    if isinstance(report, dict):
        if "summary" in report:
            return 0 if report["summary"]["failed"] == 0 else 1
        return 0 if report.get("success") else 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
