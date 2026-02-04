"""
Listener Auto-Restart Runbook
-----------------------------
Detecta listener down e executa restart automático.
Inclui verificação de status pós-restart.

Uso:
    python -m automacao.runbooks.listener_auto_restart --oracle-home /u01/app/oracle/product/19.0.0/dbhome_1
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
    from automacao.utils.alerting import send_alert
except ImportError:
    def send_alert(severity, message, details=None):
        logging.info(f"[{severity}] {message}")


class ListenerAutoRestart(BaseRunbook):
    """
    Runbook para auto-restart de Oracle Listener.
    
    Fluxo:
    1. Verifica status do listener (lsnrctl status)
    2. Se down, executa lsnrctl start
    3. Valida que voltou (lsnrctl status novamente)
    4. Notifica resultado
    """
    
    def __init__(
        self,
        oracle_home: str,
        listener_name: str = "LISTENER",
        dry_run: bool = False,
        ssh_host: Optional[str] = None,
        ssh_user: str = "oracle",
        ssh_port: int = 22,
        ssh_key_path: Optional[str] = None
    ):
        super().__init__(name="ListenerAutoRestart")
        self.oracle_home = oracle_home
        self.listener_name = listener_name
        self.dry_run = dry_run
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user
        self.ssh_port = ssh_port
        self.ssh_key_path = ssh_key_path
        self.listener_was_down = False
    
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
                # e lida melhor com double quotes em geral
                opts.append(f"-i \"{self.ssh_key_path}\"")
            
            ssh_opts = " ".join(opts)
            
            # Usar aspas duplas também para o comando remoto no Windows
            full_cmd = f"ssh {ssh_opts} {self.ssh_user}@{self.ssh_host} \"{cmd}\""
        else:
            full_cmd = cmd
        
        self.logger.debug(f"Executando: {full_cmd}")
        
        try:
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # DEBUG
            self.logger.info(f"CMD: {full_cmd}")
            self.logger.info(f"RET: {result.returncode}")
            self.logger.info(f"OUT: {result.stdout}")
            self.logger.info(f"ERR: {result.stderr}")
            
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout"
        except Exception as e:
            return -1, "", str(e)
    
    def _lsnrctl(self, action: str) -> tuple:
        """Executa lsnrctl com a ação especificada."""
        cmd = f"export ORACLE_HOME={self.oracle_home}; {self.oracle_home}/bin/lsnrctl {action} {self.listener_name}"
        return self._run_command(cmd)
    
    def validate_preconditions(self) -> bool:
        """Valida que ORACLE_HOME existe e lsnrctl está acessível."""
        self.log_step("Validando pré-condições")
        
        # Verificar se lsnrctl existe
        lsnrctl_path = f"{self.oracle_home}/bin/lsnrctl"
        
        if self.ssh_host:
            returncode, stdout, stderr = self._run_command(f"test -x {lsnrctl_path} && echo OK")
            if "OK" not in stdout:
                self.errors.append(f"lsnrctl não encontrado em {lsnrctl_path}")
                return False
        else:
            if not os.path.exists(lsnrctl_path):
                self.errors.append(f"lsnrctl não encontrado em {lsnrctl_path}")
                return False
        
        self.log_step("ORACLE_HOME válido")
        return True
    
    def execute(self) -> bool:
        """Verifica e reinicia listener se necessário."""
        self.log_step(f"Verificando status do {self.listener_name}")
        
        # 1. Verificar status
        returncode, stdout, stderr = self._lsnrctl("status")
        
        # Listener rodando = "The listener supports no services" ou "Services Summary"
        is_running = "Connecting to" in stdout and "TNS-" not in stdout
        
        if is_running:
            self.log_step(f"{self.listener_name} está UP - nenhuma ação necessária")
            self.listener_was_down = False
            return True
        
        # Listener está down
        self.listener_was_down = True
        self.logger.warning(f"[CRITICAL] {self.listener_name} está DOWN!")
        
        send_alert(
            "CRITICAL",
            f"Listener {self.listener_name} detectado DOWN",
            {"host": self.ssh_host or "localhost"}
        )
        
        if self.dry_run:
            self.log_step("[DRY-RUN] Pulando restart")
            return True
        
        # 2. Tentar restart
        self.log_step(f"Iniciando {self.listener_name}")
        returncode, stdout, stderr = self._lsnrctl("start")
        
        if returncode != 0 and "TNS-" in (stdout + stderr):
            self.errors.append(f"Falha ao iniciar listener: {stderr}")
            return False
        
        self.log_step("Comando start executado")
        return True
    
    def validate_postconditions(self) -> bool:
        """Valida que o listener está UP."""
        if not self.listener_was_down or self.dry_run:
            return True
        
        self.log_step("Validando que listener está UP")
        
        # Aguardar um pouco para o listener subir
        import time
        time.sleep(2)
        
        returncode, stdout, stderr = self._lsnrctl("status")
        
        is_running = "Connecting to" in stdout and "TNS-" not in stdout
        
        if is_running:
            self.log_step(f"{self.listener_name} está UP novamente!")
            send_alert(
                "OK",
                f"Listener {self.listener_name} reiniciado com sucesso",
                {"host": self.ssh_host or "localhost"}
            )
            return True
        else:
            self.errors.append("Listener não iniciou corretamente")
            send_alert(
                "ERROR",
                f"Falha ao reiniciar listener {self.listener_name}",
                {"stdout": stdout[:200], "stderr": stderr[:200]}
            )
            return False
    
    def rollback(self) -> bool:
        """Rollback não aplicável - start é idempotente."""
        self.log_step("Rollback não necessário (start é idempotente)")
        return True


def main():
    """Entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Listener Auto-Restart Runbook")
    parser.add_argument("--oracle-home", required=True, help="ORACLE_HOME path")
    parser.add_argument("--listener", default="LISTENER", help="Nome do listener")
    parser.add_argument("--ssh-host", help="Host remoto via SSH (opcional)")
    parser.add_argument("--ssh-user", default="oracle", help="Usuário SSH")
    parser.add_argument("--dry-run", action="store_true", help="Apenas detecta, não corrige")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    runbook = ListenerAutoRestart(
        oracle_home=args.oracle_home,
        listener_name=args.listener,
        ssh_host=args.ssh_host,
        ssh_user=args.ssh_user,
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
