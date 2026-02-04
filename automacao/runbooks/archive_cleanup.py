"""
Archive Log Cleanup Runbook
---------------------------
Limpa archive logs antigos quando FRA atinge threshold.
Usa RMAN para deleção segura respeitando política de retenção.

Uso:
    python -m automacao.runbooks.archive_cleanup --dsn localhost/orcl --threshold 80
"""
import logging
import os
import sys
import subprocess
from typing import Optional, Dict

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from automacao.runbooks.base_runbook import BaseRunbook, RunbookStatus

try:
    import cx_Oracle
except ImportError:
    cx_Oracle = None

try:
    from automacao.utils.connection import ConnectionConfig
    from automacao.utils.alerting import send_alert
except ImportError:
    ConnectionConfig = None
    def send_alert(severity, message, details=None):
        logging.info(f"[{severity}] {message}")


class ArchiveLogCleanup(BaseRunbook):
    """
    Runbook para limpeza automática de archive logs.
    
    Fluxo:
    1. Verifica uso da FRA (Flash Recovery Area)
    2. Se acima do threshold, executa RMAN DELETE
    3. Valida que o espaço foi liberado
    4. Notifica resultado
    """
    
    SQL_CHECK_FRA = """
        SELECT 
            name,
            space_limit / 1024 / 1024 as limit_mb,
            space_used / 1024 / 1024 as used_mb,
            ROUND(space_used / space_limit * 100, 2) as pct_used
        FROM v$recovery_file_dest
    """
    
    def __init__(
        self,
        config: "ConnectionConfig",
        oracle_home: str,
        threshold: int = 80,
        retention_days: int = 7,
        dry_run: bool = False,
        ssh_host: Optional[str] = None,
        ssh_user: str = "oracle",
        ssh_port: int = 22,
        ssh_key_path: Optional[str] = None
    ):
        super().__init__(name="ArchiveLogCleanup")
        self.config = config
        self.oracle_home = oracle_home
        self.threshold = threshold
        self.retention_days = retention_days
        self.dry_run = dry_run
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user
        self.ssh_port = ssh_port
        self.ssh_key_path = ssh_key_path
        self.connection: Optional[cx_Oracle.Connection] = None
        self.fra_info: Optional[Dict] = None
        self.cleanup_executed = False
    
    def _run_command(self, cmd: str) -> tuple:
        """Executa comando local ou via SSH."""
        if self.ssh_host:
            # Opções SSH
            opts = [
                "-o StrictHostKeyChecking=no",
                "-o BatchMode=yes",
                f"-p {self.ssh_port}"
            ]
            
            if self.ssh_key_path:
                # Windows requer aspas duplas para caminhos com espaços no CMD
                opts.append(f"-i \"{self.ssh_key_path}\"")
            
            ssh_opts = " ".join(opts)
            
            # Usar aspas duplas para o comando remoto (Windows safe)
            # Escapar aspas duplas internas se houver
            cmd_escaped = cmd.replace('"', '\\"')
            full_cmd = f"ssh {ssh_opts} {self.ssh_user}@{self.ssh_host} \"{cmd_escaped}\""
        else:
            full_cmd = cmd
        
        self.logger.debug(f"Executando: {full_cmd}")
        
        try:
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 min para RMAN
            )
            
            # DEBUG
            self.logger.info(f"CMD: {full_cmd}")
            self.logger.info(f"RET: {result.returncode}")
            # self.logger.info(f"OUT: {result.stdout}") # Pode ser grande
            self.logger.info(f"ERR: {result.stderr}")
            
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout"
        except Exception as e:
            return -1, "", str(e)
    
    def validate_preconditions(self) -> bool:
        """Valida conexão e FRA configurada."""
        self.log_step("Validando pré-condições")
        
        if cx_Oracle is None:
            self.errors.append("cx_Oracle não instalado")
            return False
        
        try:
            self.connection = cx_Oracle.connect(
                user=self.config.username,
                password=self.config.password,
                dsn=self.config.dsn
            )
            self.log_step("Conexão estabelecida")
            
            # Verificar FRA configurada
            cursor = self.connection.cursor()
            cursor.execute(self.SQL_CHECK_FRA)
            row = cursor.fetchone()
            cursor.close()
            
            if not row or not row[0]:
                self.errors.append("FRA não configurada")
                return False
            
            self.fra_info = {
                "name": row[0],
                "limit_mb": row[1],
                "used_mb": row[2],
                "pct_used": row[3]
            }
            
            self.log_step(f"FRA: {self.fra_info['name']} ({self.fra_info['pct_used']}% usado)")
            return True
            
        except cx_Oracle.Error as e:
            self.errors.append(f"Erro de conexão: {e}")
            return False
    
    def execute(self) -> bool:
        """Verifica e limpa archives se necessário."""
        self.log_step(f"Verificando FRA (threshold: {self.threshold}%)")
        
        if self.fra_info["pct_used"] < self.threshold:
            self.log_step(f"FRA em {self.fra_info['pct_used']}% - abaixo do threshold")
            return True
        
        # FRA acima do threshold
        self.logger.warning(
            f"[CRITICAL] FRA em {self.fra_info['pct_used']}% - acima de {self.threshold}%!"
        )
        
        send_alert(
            "WARNING",
            f"FRA em {self.fra_info['pct_used']}% - iniciando cleanup",
            {"limit_mb": self.fra_info["limit_mb"], "used_mb": self.fra_info["used_mb"]}
        )
        
        if self.dry_run:
            self.log_step("[DRY-RUN] Pulando RMAN delete")
            return True
        
        # Executar RMAN para limpar archives
        return self._run_rman_cleanup()
    
    def _run_rman_cleanup(self) -> bool:
        """Executa RMAN para deletar archives antigos."""
        self.log_step(f"Executando RMAN delete (retenção: {self.retention_days} dias)")
        
        # Script RMAN
        # Script RMAN (Usando pipe para evitar problemas com heredoc via SSH/Windows)
        rman_cmds = (
            f"DELETE NOPROMPT ARCHIVELOG ALL COMPLETED BEFORE 'SYSDATE-{self.retention_days}'; "
            "CROSSCHECK ARCHIVELOG ALL; "
            "DELETE NOPROMPT EXPIRED ARCHIVELOG ALL; "
            "EXIT;"
        )
        
        cmd_wrapper = (
            f"export ORACLE_HOME={self.oracle_home} && "
            f"export ORACLE_SID={self.config.dsn.split('/')[-1]} && "
            f"echo \"{rman_cmds}\" | {self.oracle_home}/bin/rman target /"
        )
        
        returncode, stdout, stderr = self._run_command(cmd_wrapper)
        
        if returncode != 0:
            self.errors.append(f"RMAN falhou: {stderr}")
            return False
        
        # Verificar output do RMAN
        if "deleted" in stdout.lower() or "RMAN-" not in stdout:
            self.log_step("RMAN cleanup executado")
            self.cleanup_executed = True
            return True
        else:
            self.errors.append(f"RMAN output inesperado: {stdout[:200]}")
            return False
    
    def validate_postconditions(self) -> bool:
        """Valida que o espaço foi liberado."""
        if not self.cleanup_executed or self.dry_run:
            return True
        
        self.log_step("Validando pós-condições")
        
        cursor = self.connection.cursor()
        cursor.execute(self.SQL_CHECK_FRA)
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            new_pct = row[3]
            freed_mb = self.fra_info["used_mb"] - row[2]
            
            self.log_step(f"FRA agora em {new_pct}% (liberado: {freed_mb:.0f}MB)")
            
            send_alert(
                "OK",
                f"Archive cleanup concluído - FRA agora em {new_pct}%",
                {"freed_mb": freed_mb, "retention_days": self.retention_days}
            )
            
            return new_pct < self.fra_info["pct_used"]  # Deve ter diminuído
        
        return True
    
    def rollback(self) -> bool:
        """Rollback não aplicável - archives deletados são gone."""
        self.log_step("Rollback não aplicável (archives já deletados)")
        return True


def main():
    """Entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Archive Log Cleanup Runbook")
    parser.add_argument("--dsn", help="DSN (Default: env ORACLE_DSN)")
    parser.add_argument("--user", help="User (Default: env ORACLE_USER)")
    parser.add_argument("--password", help="Password (Default: env ORACLE_PASSWORD)")
    parser.add_argument("--oracle-home", required=True, help="ORACLE_HOME path")
    parser.add_argument("--threshold", type=int, default=80, help="% threshold (default: 80)")
    parser.add_argument("--retention", type=int, default=7, help="Dias de retenção (default: 7)")
    parser.add_argument("--ssh-host", help="Host remoto via SSH")
    parser.add_argument("--ssh-port", type=int, default=22, help="Porta SSH (default: 22)")
    parser.add_argument("--ssh-key-path", help="Caminho chave privada SSH")
    parser.add_argument("--dry-run", action="store_true", help="Apenas detecta, não corrige")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
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
    
    runbook = ArchiveLogCleanup(
        config=config,
        oracle_home=args.oracle_home,
        threshold=args.threshold,
        retention_days=args.retention,
        ssh_host=args.ssh_host,
        ssh_user=args.user or "oracle", # Assumindo user oracle para SSH se não especificado diferente
        ssh_port=args.ssh_port,
        ssh_key_path=args.ssh_key_path,
        dry_run=args.dry_run
    )
    
    result = runbook.run()
    
    print("\n" + "=" * 60)
    print(f"RESULTADO: {result['status']}")
    print(f"Steps: {len(result['steps_executed'])}")
    if result['errors']:
        print(f"Erros: {result['errors']}")
    print("=" * 60)
    
    return 0 if result['success'] else 1


if __name__ == "__main__":
    sys.exit(main())
