"""
ORAEX - Oracle Health Check Automation
---------------------------------------
Verifica saúde do banco Oracle seguindo padrões DBRE.
Baseado no BOOK DBA Getnet.

Uso:
    python oracle_healthcheck.py --user system --dsn localhost:1521/orcl
"""
import logging
import argparse
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Optional, List, Tuple, Dict

import cx_Oracle





# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

class CheckStatus(Enum):
    """Status possíveis de um check."""
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"


class CheckResult:
    """Resultado padronizado de um check."""
    def __init__(self, name: str, status: CheckStatus, message: str, details: Optional[dict] = None):
        self.name = name
        self.status = status
        self.message = message
        self.details = details

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details
        }


class ConnectionConfig:
    """Configuração de conexão com o banco."""
    def __init__(self, username: str, password: str, dsn: str, encoding: str = "UTF-8"):
        self.username = username
        self.password = password
        self.dsn = dsn
        self.encoding = encoding


# =============================================================================
# LOGGING
# =============================================================================

def setup_logging(log_file: str = "healthcheck.log") -> None:
    """Configura logging para arquivo e console (stderr)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler(log_file, encoding="utf-8")
        ]
    )


# =============================================================================
# BASE CHECKER (ABSTRAÇÃO)
# =============================================================================

class BaseChecker(ABC):
    """Interface base para todos os checkers."""
    
    @abstractmethod
    def run(self, connection: cx_Oracle.Connection) -> CheckResult:
        """Executa o check e retorna resultado."""
        pass

    def execute_query(
        self, 
        connection: cx_Oracle.Connection, 
        sql: str, 
        params: dict = None
    ) -> List[Tuple]:
        """Executa SQL de forma segura e retorna resultados."""
        cursor = connection.cursor()
        try:
            cursor.execute(sql, params or {})
            return cursor.fetchall()
        finally:
            cursor.close()

    def execute_scalar(
        self, 
        connection: cx_Oracle.Connection, 
        sql: str
    ) -> Optional[str]:
        """Executa SQL e retorna valor único."""
        rows = self.execute_query(connection, sql)
        return rows[0][0] if rows else None


# =============================================================================
# CHECKERS ESPECÍFICOS
# =============================================================================

class BlockingSessionsChecker(BaseChecker):
    """Verifica sessões bloqueadoras."""
    
    SQL_LOCKS = """
        SELECT s.sid, s.serial#, s.username, s.status, 
               s.blocking_session, o.owner || '.' || o.object_name
        FROM v$session s
        LEFT JOIN v$locked_object lo ON s.sid = lo.session_id
        LEFT JOIN dba_objects o ON o.object_id = lo.object_id
        WHERE s.blocking_session IS NOT NULL
        ORDER BY s.sid
    """

    def run(self, connection: cx_Oracle.Connection) -> CheckResult:
        try:
            locks = self.execute_query(connection, self.SQL_LOCKS)
            
            if not locks:
                return CheckResult(
                    name="Blocking Sessions",
                    status=CheckStatus.OK,
                    message="Nenhuma sessão bloqueadora encontrada."
                )
            
            details = [
                {"sid": r[0], "serial": r[1], "user": r[2], "blocker": r[4]}
                for r in locks
            ]
            return CheckResult(
                name="Blocking Sessions",
                status=CheckStatus.CRITICAL,
                message=f"{len(locks)} sessão(ões) bloqueada(s) encontrada(s).",
                details={"sessions": details}
            )
            
        except cx_Oracle.Error as e:
            return CheckResult(
                name="Blocking Sessions",
                status=CheckStatus.ERROR,
                message=f"Erro ao verificar: {e}"
            )


class RMANStatusChecker(BaseChecker):
    """Verifica status dos backups RMAN."""
    
    SQL_RMAN = """
        SELECT start_time, operation, object_type, status,
               ROUND(input_bytes/1024/1024) input_mb
        FROM v$rman_status
        WHERE start_time > SYSDATE - 1
          AND operation IN ('BACKUP', 'RESTORE', 'RECOVER')
        ORDER BY start_time DESC
    """

    def run(self, connection: cx_Oracle.Connection) -> CheckResult:
        try:
            backups = self.execute_query(connection, self.SQL_RMAN)
            
            if not backups:
                return CheckResult(
                    name="RMAN Backup",
                    status=CheckStatus.WARNING,
                    message="Nenhum backup nas últimas 24h."
                )
            
            failed = [b for b in backups if b[3] not in ("COMPLETED", "RUNNING")]
            if failed:
                return CheckResult(
                    name="RMAN Backup",
                    status=CheckStatus.CRITICAL,
                    message=f"{len(failed)} backup(s) com falha.",
                    details={"failed": [b[3] for b in failed]}
                )
            
            return CheckResult(
                name="RMAN Backup",
                status=CheckStatus.OK,
                message=f"{len(backups)} backup(s) OK nas últimas 24h."
            )
            
        except cx_Oracle.Error as e:
            return CheckResult(
                name="RMAN Backup",
                status=CheckStatus.ERROR,
                message=f"Erro: {e}"
            )


class ComplianceChecker(BaseChecker):
    """Verifica conformidade com Book DBA Getnet."""
    
    PARAMS = {"recyclebin": "OFF"}

    def run(self, connection: cx_Oracle.Connection) -> CheckResult:
        issues = []
        
        try:
            # Force Logging
            fl = self.execute_scalar(connection, "SELECT force_logging FROM v$database")
            if fl != "YES":
                issues.append(f"FORCE_LOGGING={fl} (esperado YES)")

            # Recyclebin
            rb = self.execute_scalar(
                connection, 
                "SELECT value FROM v$parameter WHERE name='recyclebin'"
            )
            if rb and rb.upper() != "OFF":
                issues.append(f"recyclebin={rb} (esperado OFF)")

            # SPFILE
            sp = self.execute_scalar(
                connection,
                "SELECT value FROM v$parameter WHERE name='spfile'"
            )
            if not sp:
                issues.append("SPFILE não configurado")

            if issues:
                return CheckResult(
                    name="Compliance",
                    status=CheckStatus.WARNING,
                    message=f"{len(issues)} violação(ões) encontrada(s).",
                    details={"issues": issues}
                )
            
            return CheckResult(
                name="Compliance",
                status=CheckStatus.OK,
                message="Todos os parâmetros em conformidade."
            )

        except cx_Oracle.Error as e:
            return CheckResult(
                name="Compliance",
                status=CheckStatus.ERROR,
                message=f"Erro: {e}"
            )


class TDEWalletChecker(BaseChecker):
    """Verifica status da Wallet TDE."""
    
    SQL_WALLET = """
        SELECT wrl_type, status, wallet_type 
        FROM v$encryption_wallet WHERE ROWNUM = 1
    """

    def run(self, connection: cx_Oracle.Connection) -> CheckResult:
        try:
            wallet = self.execute_query(connection, self.SQL_WALLET)
            
            if not wallet:
                return CheckResult(
                    name="TDE Wallet",
                    status=CheckStatus.OK,
                    message="TDE não configurado neste ambiente."
                )
            
            wrl_type, status, wallet_type = wallet[0]
            if status == "OPEN":
                msg = f"Wallet aberta. Tipo: {wallet_type}"
                if wallet_type == "AUTOLOGIN":
                    msg += " (Auto Login ativado)"
                
                return CheckResult(
                    name="TDE Wallet",
                    status=CheckStatus.OK,
                    message=msg
                )
            
            if status == "OPEN_NO_MASTER_KEY":
                 return CheckResult(
                    name="TDE Wallet",
                    status=CheckStatus.WARNING,
                    message=f"Wallet aberta mas sem Master Key definida. Tipo: {wallet_type}"
                )
            
            return CheckResult(
                name="TDE Wallet",
                status=CheckStatus.CRITICAL,
                message=f"Wallet NÃO está aberta! Status: {status}"
            )

        except cx_Oracle.Error as e:
            err_code = e.args[0].code if e.args else 0
            if err_code == 942:
                return CheckResult(
                    name="TDE Wallet",
                    status=CheckStatus.OK,
                    message="TDE não disponível (Oracle 11g ou anterior)."
                )
            return CheckResult(
                name="TDE Wallet",
                status=CheckStatus.ERROR,
                message=f"Erro: {e}"
            )


class ASHTopWaitsChecker(BaseChecker):
    """Analisa top waits do ASH."""
    
    SQL_ASH = """
        SELECT NVL(event, session_state), COUNT(*)
        FROM v$active_session_history
        WHERE sample_time >= SYSTIMESTAMP - INTERVAL '5' MINUTE
        GROUP BY NVL(event, session_state)
        ORDER BY 2 DESC
        FETCH FIRST 5 ROWS ONLY
    """

    def run(self, connection: cx_Oracle.Connection) -> CheckResult:
        try:
            waits = self.execute_query(connection, self.SQL_ASH)
            
            if not waits:
                return CheckResult(
                    name="ASH Top Waits",
                    status=CheckStatus.OK,
                    message="Sem atividade significativa nos últimos 5 min."
                )
            
            top_event = waits[0][0]
            return CheckResult(
                name="ASH Top Waits",
                status=CheckStatus.OK,
                message=f"Top evento: {top_event}",
                details={"waits": [{"event": w[0], "samples": w[1]} for w in waits]}
            )

        except cx_Oracle.Error as e:
            return CheckResult(
                name="ASH Top Waits",
                status=CheckStatus.WARNING,
                message="ASH indisponível (licença ou versão)."
            )


# =============================================================================
# ORQUESTRADOR PRINCIPAL
# =============================================================================

class OracleHealthCheck:
    """Orquestrador que executa todos os checkers."""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.connection: Optional[cx_Oracle.Connection] = None
        self.results: List[CheckResult] = []
        self.checkers: List[BaseChecker] = [
            BlockingSessionsChecker(),
            RMANStatusChecker(),
            ComplianceChecker(),
            TDEWalletChecker(),
            ASHTopWaitsChecker(),
        ]

    def connect(self) -> bool:
        """Estabelece conexão com o banco."""
        try:
            self.connection = cx_Oracle.connect(
                user=self.config.username,
                password=self.config.password,
                dsn=self.config.dsn,
                encoding=self.config.encoding
            )
            logging.info(f"Conectado a {self.config.dsn}")
            return True
        except cx_Oracle.Error as e:
            logging.error(f"Falha na conexão: {e}")
            return False

    def run_all_checks(self) -> List[CheckResult]:
        """Executa todos os checkers registrados."""
        if not self.connect():
            return []

        for checker in self.checkers:
            result = checker.run(self.connection)
            self.results.append(result)
            self._log_result(result)

        return self.results

    def _log_result(self, result: CheckResult) -> None:
        """Loga resultado com nível apropriado."""
        log_map = {
            CheckStatus.OK: logging.info,
            CheckStatus.WARNING: logging.warning,
            CheckStatus.CRITICAL: logging.error,
            CheckStatus.ERROR: logging.error,
        }
        log_fn = log_map.get(result.status, logging.info)
        log_fn(f"[{result.status.value}] {result.name}: {result.message}")

    def get_summary(self) -> dict:
        """Retorna resumo dos checks."""
        return {
            "total": len(self.results),
            "ok": sum(1 for r in self.results if r.status == CheckStatus.OK),
            "warnings": sum(1 for r in self.results if r.status == CheckStatus.WARNING),
            "critical": sum(1 for r in self.results if r.status == CheckStatus.CRITICAL),
            "errors": sum(1 for r in self.results if r.status == CheckStatus.ERROR),
        }


# =============================================================================
# ENTRY POINT
# =============================================================================

def main() -> int:
    """Ponto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="ORAEX - Oracle Health Check Automation"
    )
    parser.add_argument("--user", default="system", help="Usuário do banco")
    parser.add_argument("--password", default="oracle", help="Senha")
    parser.add_argument("--dsn", default="localhost:1521/orcl", help="DSN")
    parser.add_argument("--log-file", default="healthcheck.log", help="Arquivo de log")
    parser.add_argument("--json", action="store_true", help="Output em formato JSON")
    
    args = parser.parse_args()
    setup_logging(args.log_file)



    config = ConnectionConfig(
        username=args.user,
        password=args.password,
        dsn=args.dsn
    )

    checker = OracleHealthCheck(config)
    results = checker.run_all_checks()
    summary = checker.get_summary()

    # Prepara objeto de dados completo
    final_output = {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "results": [r.to_dict() for r in results]
    }

    if args.json:
        import json
        print(json.dumps(final_output, indent=2))
        return 0

    logging.info(f"Resumo: {summary['ok']} OK, {summary['warnings']} Warnings, "
                 f"{summary['critical']} Critical, {summary['errors']} Errors")

    # Exit code: 0 se tudo OK, 1 se há warnings, 2 se há critical/errors
    if summary["critical"] or summary["errors"]:
        return 2
    if summary["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
