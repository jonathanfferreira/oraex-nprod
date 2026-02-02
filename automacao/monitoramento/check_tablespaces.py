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
    def __init__(self, name: str, total_mb: float, used_mb: float, free_mb: float, pct_used: float, file_name: str):
        self.name = name
        self.total_mb = total_mb
        self.used_mb = used_mb
        self.free_mb = free_mb
        self.pct_used = pct_used
        self.file_name = file_name

    @property
    def is_critical(self) -> bool:
        return self.pct_used >= 95

    @property
    def is_warning(self) -> bool:
        return 85 <= self.pct_used < 95

    def get_resize_command(self, add_mb: int = 1024) -> str:
        """Gera comando ALTER DATABASE para resize."""
        new_size = int(self.total_mb + add_mb)
        return f"ALTER DATABASE DATAFILE '{self.file_name}' RESIZE {new_size}M;"


class TablespaceChecker:
    """Verifica uso de tablespaces."""

    SQL_USAGE = """
        SELECT 
            df.tablespace_name,
            ROUND(df.total_mb, 2),
            ROUND(df.total_mb - NVL(fs.free_mb, 0), 2),
            ROUND(NVL(fs.free_mb, 0), 2),
            ROUND(((df.total_mb - NVL(fs.free_mb, 0)) / df.total_mb) * 100, 2),
            df.file_name
        FROM 
            (SELECT tablespace_name, file_id, file_name, 
                    SUM(bytes)/1024/1024 AS total_mb 
             FROM dba_data_files 
             GROUP BY tablespace_name, file_id, file_name) df
        LEFT JOIN 
            (SELECT tablespace_name, file_id, 
                    SUM(bytes)/1024/1024 AS free_mb 
             FROM dba_free_space 
             GROUP BY tablespace_name, file_id) fs
        ON df.tablespace_name = fs.tablespace_name 
           AND df.file_id = fs.file_id
        WHERE ROUND(((df.total_mb - NVL(fs.free_mb,0)) / df.total_mb) * 100, 2) >= :threshold
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
                    free_mb=r[3], pct_used=r[4], file_name=r[5]
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


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="ORAEX - Tablespace Monitor"
    )
    parser.add_argument("--dsn", default="localhost/ORCL", help="DSN")
    parser.add_argument("--user", default="system", help="User")
    parser.add_argument("--password", default="oracle", help="Password")
    parser.add_argument("--threshold", type=int, default=90, help="% threshold")

    args = parser.parse_args()
    setup_logging()

    checker = TablespaceChecker(
        dsn=args.dsn,
        user=args.user,
        password=args.password,
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
