"""
ORAEX - RMAN Backup Manager
---------------------------
Gerenciador de backups RMAN com suporte a:
- Backup Full, Incremental Level 0/1, Archivelog
- Catálogo RMAN ou Control File
- Validação via V$RMAN_BACKUP_JOB_DETAILS
- Output JSON para integração

Uso:
    python rman_backup_manager.py --type full
    python rman_backup_manager.py --type incremental --level 1
    python rman_backup_manager.py --status --days 7
"""
import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any

# Tentar importar cx_Oracle, mas permitir mock para testes
try:
    import cx_Oracle
except ImportError:
    cx_Oracle = None


class BackupType(Enum):
    FULL = "full"
    INCREMENTAL_L0 = "incremental_l0"
    INCREMENTAL_L1 = "incremental_l1"
    ARCHIVELOG = "archivelog"
    VALIDATE = "validate"


class BackupStatus(Enum):
    COMPLETED = "COMPLETED"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    COMPLETED_WITH_WARNINGS = "COMPLETED WITH WARNINGS"


class BackupJob:
    """Representa um job de backup RMAN."""
    def __init__(self, session_key: int, start_time: datetime, end_time: Optional[datetime], status: str, input_type: str, output_bytes: int, elapsed_seconds: int):
        self.session_key = session_key
        self.start_time = start_time
        self.end_time = end_time
        self.status = status
        self.input_type = input_type
        self.output_bytes = output_bytes
        self.elapsed_seconds = elapsed_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_key": self.session_key,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "input_type": self.input_type,
            "output_bytes": self.output_bytes,
            "output_gb": round(self.output_bytes / (1024**3), 2),
            "elapsed_seconds": self.elapsed_seconds,
            "elapsed_minutes": round(self.elapsed_seconds / 60, 1)
        }


class BackupResult:
    """Resultado de uma operação de backup."""
    def __init__(self, success: bool, backup_type: str, message: str, start_time: datetime, end_time: Optional[datetime] = None, output_path: Optional[str] = None, error: Optional[str] = None):
        self.success = success
        self.backup_type = backup_type
        self.message = message
        self.start_time = start_time
        self.end_time = end_time
        self.output_path = output_path
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "backup_type": self.backup_type,
            "message": self.message,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "output_path": self.output_path,
            "error": self.error
        }


class RMANExecutor:
    """Executa comandos RMAN."""
    
    def __init__(self, oracle_home: str, oracle_sid: str, 
                 catalog_conn: Optional[str] = None):
        self.oracle_home = Path(oracle_home)
        self.oracle_sid = oracle_sid
        self.catalog_conn = catalog_conn
        self.rman_path = self.oracle_home / "bin" / "rman"
    
    def _build_connect_string(self) -> str:
        """Constrói string de conexão RMAN."""
        if self.catalog_conn:
            return f"target / catalog {self.catalog_conn}"
        return "target /"
    
    def execute(self, script: str, timeout: int = 7200) -> tuple[bool, str]:
        """Executa script RMAN. Retorna (sucesso, output)."""
        env = os.environ.copy()
        env["ORACLE_HOME"] = str(self.oracle_home)
        env["ORACLE_SID"] = self.oracle_sid
        env["PATH"] = f"{self.oracle_home}/bin:{env.get('PATH', '')}"
        
        full_script = f"""
        connect {self._build_connect_string()}
        {script}
        exit;
        """
        
        try:
            result = subprocess.run(
                [str(self.rman_path)],
                input=full_script,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            
            success = result.returncode == 0 and "RMAN-" not in result.stdout
            return success, result.stdout + result.stderr
            
        except subprocess.TimeoutExpired:
            return False, f"Timeout após {timeout} segundos"
        except Exception as e:
            return False, str(e)


class RMANBackupManager:
    """Gerenciador de backups RMAN."""
    
    BACKUP_SCRIPTS = {
        BackupType.FULL: """
            run {{
                allocate channel c1 device type disk;
                allocate channel c2 device type disk;
                backup as compressed backupset 
                    full database 
                    format '{backup_dest}/full_%d_%T_%U'
                    tag 'ORAEX_FULL_{date}';
                backup current controlfile format '{backup_dest}/ctl_%d_%T_%U';
                backup spfile format '{backup_dest}/spf_%d_%T_%U';
                release channel c1;
                release channel c2;
            }}
        """,
        BackupType.INCREMENTAL_L0: """
            run {{
                allocate channel c1 device type disk;
                allocate channel c2 device type disk;
                backup as compressed backupset 
                    incremental level 0 database 
                    format '{backup_dest}/incr0_%d_%T_%U'
                    tag 'ORAEX_INCR0_{date}';
                release channel c1;
                release channel c2;
            }}
        """,
        BackupType.INCREMENTAL_L1: """
            run {{
                allocate channel c1 device type disk;
                allocate channel c2 device type disk;
                backup as compressed backupset 
                    incremental level 1 database 
                    format '{backup_dest}/incr1_%d_%T_%U'
                    tag 'ORAEX_INCR1_{date}';
                release channel c1;
                release channel c2;
            }}
        """,
        BackupType.ARCHIVELOG: """
            run {{
                allocate channel c1 device type disk;
                backup as compressed backupset 
                    archivelog all not backed up
                    format '{backup_dest}/arch_%d_%T_%U'
                    tag 'ORAEX_ARCH_{date}'
                    delete input;
                release channel c1;
            }}
        """,
        BackupType.VALIDATE: """
            restore database validate;
            restore archivelog all validate;
        """
    }
    
    def __init__(self, executor: RMANExecutor, backup_dest: str):
        self.executor = executor
        self.backup_dest = Path(backup_dest)
    
    def run_backup(self, backup_type: BackupType) -> BackupResult:
        """Executa backup do tipo especificado."""
        start_time = datetime.now()
        date_str = start_time.strftime("%Y%m%d")
        
        script_template = self.BACKUP_SCRIPTS.get(backup_type)
        if not script_template:
            return BackupResult(
                success=False,
                backup_type=backup_type.value,
                message="Tipo de backup não suportado",
                start_time=start_time,
                error="Invalid backup type"
            )
        
        script = script_template.format(
            backup_dest=self.backup_dest,
            date=date_str
        )
        
        logging.info(f"Iniciando backup {backup_type.value}...")
        success, output = self.executor.execute(script)
        end_time = datetime.now()
        
        if success:
            logging.info(f"Backup {backup_type.value} concluído com sucesso!")
            return BackupResult(
                success=True,
                backup_type=backup_type.value,
                message=f"Backup {backup_type.value} concluído",
                start_time=start_time,
                end_time=end_time,
                output_path=str(self.backup_dest)
            )
        else:
            logging.error(f"Backup {backup_type.value} falhou!")
            return BackupResult(
                success=False,
                backup_type=backup_type.value,
                message=f"Backup {backup_type.value} falhou",
                start_time=start_time,
                end_time=end_time,
                error=output[:500]  # Primeiros 500 chars do erro
            )


class BackupStatusChecker:
    """Verifica status de backups via V$RMAN_BACKUP_JOB_DETAILS."""
    
    QUERY = """
        SELECT 
            SESSION_KEY,
            START_TIME,
            END_TIME,
            STATUS,
            INPUT_TYPE,
            NVL(OUTPUT_BYTES, 0) as OUTPUT_BYTES,
            NVL(ELAPSED_SECONDS, 0) as ELAPSED_SECONDS
        FROM V$RMAN_BACKUP_JOB_DETAILS
        WHERE START_TIME >= SYSDATE - :days
        ORDER BY START_TIME DESC
    """
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    def get_backup_history(self, days: int = 7) -> List[BackupJob]:
        """Retorna histórico de backups dos últimos N dias."""
        if not cx_Oracle:
            logging.warning("cx_Oracle não disponível, retornando lista vazia")
            return []
        
        try:
            with cx_Oracle.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(self.QUERY, {"days": days})
                
                jobs = []
                for row in cursor:
                    jobs.append(BackupJob(
                        session_key=row[0],
                        start_time=row[1],
                        end_time=row[2],
                        status=row[3],
                        input_type=row[4],
                        output_bytes=row[5],
                        elapsed_seconds=row[6]
                    ))
                return jobs
                
        except Exception as e:
            logging.error(f"Erro ao consultar histórico: {e}")
            return []
    
    def get_last_successful(self, input_type: str = "DB FULL") -> Optional[BackupJob]:
        """Retorna último backup bem-sucedido do tipo especificado."""
        jobs = self.get_backup_history(days=30)
        for job in jobs:
            if job.status == "COMPLETED" and job.input_type == input_type:
                return job
        return None


def setup_logging(verbose: bool = False) -> None:
    """Configura logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)]
    )


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="ORAEX - RMAN Backup Manager"
    )
    
    # Ações
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--type", 
        choices=["full", "incremental", "archivelog", "validate"],
        help="Tipo de backup a executar"
    )
    group.add_argument(
        "--status",
        action="store_true",
        help="Exibir status dos backups recentes"
    )
    
    # Opções
    parser.add_argument(
        "--level", 
        type=int, 
        choices=[0, 1],
        default=1,
        help="Nível do incremental (0 ou 1)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Dias de histórico para --status"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output em formato JSON"
    )
    parser.add_argument(
        "--oracle-home",
        default=os.environ.get("ORACLE_HOME", "/u01/app/oracle/product/19.0.0/dbhome_1"),
        help="ORACLE_HOME"
    )
    parser.add_argument(
        "--oracle-sid",
        default=os.environ.get("ORACLE_SID", "ORCL"),
        help="ORACLE_SID"
    )
    parser.add_argument(
        "--backup-dest",
        default="/u02/backup",
        help="Diretório de destino dos backups"
    )
    parser.add_argument(
        "--catalog",
        help="Connection string do catálogo RMAN (opcional)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Modo verbose"
    )
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    if args.status:
        # Modo status - mostrar histórico
        checker = BackupStatusChecker("/")  # Conexão local
        jobs = checker.get_backup_history(args.days)
        
        if args.json:
            print(json.dumps([j.to_dict() for j in jobs], indent=2))
        else:
            print(f"\n{'='*70}")
            print(f"HISTÓRICO DE BACKUPS (Últimos {args.days} dias)")
            print(f"{'='*70}")
            for job in jobs:
                status_icon = "✅" if job.status == "COMPLETED" else "❌"
                print(f"{status_icon} [{job.start_time}] {job.input_type:<15} "
                      f"{job.status:<20} {job.to_dict()['output_gb']:.1f} GB")
            print(f"{'='*70}")
            print(f"Total: {len(jobs)} backups")
        
        return 0
    
    # Modo backup
    executor = RMANExecutor(
        oracle_home=args.oracle_home,
        oracle_sid=args.oracle_sid,
        catalog_conn=args.catalog
    )
    
    manager = RMANBackupManager(
        executor=executor,
        backup_dest=args.backup_dest
    )
    
    # Determinar tipo de backup
    if args.type == "full":
        backup_type = BackupType.FULL
    elif args.type == "incremental":
        backup_type = BackupType.INCREMENTAL_L0 if args.level == 0 else BackupType.INCREMENTAL_L1
    elif args.type == "archivelog":
        backup_type = BackupType.ARCHIVELOG
    else:
        backup_type = BackupType.VALIDATE
    
    result = manager.run_backup(backup_type)
    
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        icon = "✅" if result.success else "❌"
        print(f"\n{icon} {result.message}")
        if result.error:
            print(f"Erro: {result.error}")
    
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
