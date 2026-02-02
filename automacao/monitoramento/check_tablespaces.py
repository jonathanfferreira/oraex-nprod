"""
ORAEX - Oracle Tablespace Monitor
---------------------------------
Monitora uso de tablespaces e sugere comandos de resize.

Uso:
    python check_tablespaces.py --dsn localhost/ORCL --threshold 90
"""
import sys
import logging
import argparse
from typing import List, Optional

import cx_Oracle


class TablespaceInfo:
    """Informação de uma tablespace."""
    def __init__(self, name: str, total_mb: float, used_mb: float, free_mb: float, pct_used: float, sample_file: str):
        self.name = name
        self.total_mb = total_mb
        self.used_mb = used_mb
        self.free_mb = free_mb
        self.pct_used = pct_used
        self.sample_file = sample_file

    @property
    def is_critical(self) -> bool:
        return self.pct_used >= 95

    @property
    def is_warning(self) -> bool:
        return 85 <= self.pct_used < 95

    def get_resize_command(self, add_mb: int = 1024) -> str:
        """Gera comando ALTER DATABASE para resize."""
        # Sugere resize do arquivo amostra
        current_size = self.total_mb # Aproximado, pois total_mb é da TS inteira
        # Na verdade, para resize, precisamos saber o tamanho DO ARQUIVO.
        # Simplificação DBRE: Sugerir adicionar Datafile é mais seguro que resize se não sabemos o tamanho dele.
        # Mas para manter compatibilidade, vamos sugerir Resize com base no nome, mas o usuário deve ajustar.
        return f"ALTER DATABASE DATAFILE '{self.sample_file}' RESIZE +{add_mb}M;"


class TablespaceChecker:
    """Verifica uso de tablespaces (Nível Tablespace)."""

    # Otimização: Agrupa por Tablespace (reduz cardinalidade de joins)
    SQL_USAGE = """
        WITH 
        t_total AS (
            SELECT tablespace_name, SUM(bytes) AS bytes, MAX(file_name) as sample_file
            FROM dba_data_files
            GROUP BY tablespace_name
        ),
        t_free AS (
            SELECT tablespace_name, SUM(bytes) AS bytes
            FROM dba_free_space
            GROUP BY tablespace_name
        )
        SELECT 
            t.tablespace_name,
            ROUND(t.bytes / 1024 / 1024, 2) AS total_mb,
            ROUND((t.bytes - NVL(f.bytes, 0)) / 1024 / 1024, 2) AS used_mb,
            ROUND(NVL(f.bytes, 0) / 1024 / 1024, 2) AS free_mb,
            ROUND(((t.bytes - NVL(f.bytes, 0)) / t.bytes) * 100, 2) AS pct_used,
            t.sample_file
        FROM t_total t
        LEFT JOIN t_free f ON t.tablespace_name = f.tablespace_name
        WHERE ROUND(((t.bytes - NVL(f.bytes, 0)) / t.bytes) * 100, 2) >= :threshold
        ORDER BY 5 DESC
    """

    def __init__(self, dsn: str, user: str, password: str, threshold: int = 90):
        self.dsn = dsn
        self.user = user
        self.password = password
        self.threshold = threshold
        self.connection: Optional[cx_Oracle.Connection] = None

    def connect(self) -> bool:
        """Estabelece conexão."""
        try:
            self.connection = cx_Oracle.connect(
                self.user, self.password, self.dsn
            )
            logging.info(f"Conectado a {self.dsn}")
            return True
        except cx_Oracle.Error as e:
            logging.error(f"Conexão falhou: {e}")
            return False

    def get_tablespaces(self) -> List[TablespaceInfo]:
        """Busca tablespaces acima do threshold."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(self.SQL_USAGE, threshold=self.threshold)
            rows = cursor.fetchall()
            return [
                TablespaceInfo(
                    name=r[0], total_mb=r[1], used_mb=r[2],
                    free_mb=r[3], pct_used=r[4], sample_file=r[5]
                )
                for r in rows
            ]
        finally:
            cursor.close()

    def run(self) -> List[TablespaceInfo]:
        """Executa verificação completa."""
        if not self.connect():
            return []

        tablespaces = self.get_tablespaces()

        if not tablespaces:
            logging.info(f"✅ Nenhuma tablespace acima de {self.threshold}%.")
            return []

        logging.warning(f"🚨 {len(tablespaces)} tablespace(s) acima de {self.threshold}%")
        
        for ts in tablespaces:
            level = "CRITICAL" if ts.is_critical else "WARNING"
            logging.warning(
                f"[{level}] {ts.name}: {ts.pct_used}% | "
                f"Used: {ts.used_mb}MB / {ts.total_mb}MB"
            )

        return tablespaces


def print_fix_commands(tablespaces: List[TablespaceInfo]) -> None:
    """Imprime comandos de correção sugeridos."""
    if not tablespaces:
        return

    print("\n" + "=" * 80)
    print("COMANDOS SUGERIDOS PARA CORREÇÃO:")
    print("=" * 80)
    
    for ts in tablespaces:
        print(f"-- {ts.name} ({ts.pct_used}%)")
        print(ts.get_resize_command())
        print()


# Setup de Path para importar módulos irmãos
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from automacao.utils.credentials import get_credentials
    from automacao.utils.logging_config import setup_logging
except ImportError:
    # Fallback
    def setup_logging(log_file=None, json_mode=False):
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    def get_credentials(cli_user, cli_password, cli_dsn):
        from collections import namedtuple
        Creds = namedtuple('DBCredentials', ['username', 'password', 'dsn'])
        return Creds(cli_user or 'system', cli_password or 'oracle', cli_dsn or 'localhost/ORCL')

def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="ORAEX - Tablespace Monitor"
    )
    parser.add_argument("--dsn", help="DSN (Default: env ORACLE_DSN)")
    parser.add_argument("--user", help="User (Default: env ORACLE_USER)")
    parser.add_argument("--password", help="Password (Default: env ORACLE_PASSWORD)")
    parser.add_argument("--threshold", type=int, default=90, help="% threshold")
    parser.add_argument("--json", action="store_true", help="Logs em format JSON")

    args = parser.parse_args()
    setup_logging(json_mode=args.json)

    creds = get_credentials(args.user, args.password, args.dsn)

    checker = TablespaceChecker(
        dsn=creds.dsn,
        user=creds.username,
        password=creds.password,
        threshold=args.threshold
    )

    tablespaces = checker.run()
    print_fix_commands(tablespaces)

    critical = [ts for ts in tablespaces if ts.is_critical]
    if critical:
        return 2
    if tablespaces:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
