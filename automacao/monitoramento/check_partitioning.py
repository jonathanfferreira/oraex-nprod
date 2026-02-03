"""
ORAEX - Oracle Partitioning Monitor
-----------------------------------
Verifica se partições futuras existem para tabelas RANGE particionadas.
Previne erro ORA-14400: inserted partition key does not map.

Uso:
    python check_partitioning.py --dsn host:1521/orcl --user sys --password pwd
"""
import sys
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import cx_Oracle

# ConnectionConfig importado de utils.connection (centralizado)


class PartitionInfo:
    """Informação de uma partição."""
    def __init__(self, owner: str, table_name: str, high_value_date: Optional[datetime], is_interval: bool, days_ahead: int):
        self.owner = owner
        self.table_name = table_name
        self.high_value_date = high_value_date
        self.is_interval = is_interval
        self.days_ahead = days_ahead


class PartitionChecker:
    """Verifica partições futuras em tabelas RANGE."""

    SQL_TABLES = """
        SELECT owner, table_name, interval 
        FROM dba_part_tables 
        WHERE owner NOT IN ('SYS', 'SYSTEM', 'SYSMAN', 'MDSYS', 'XDB', 'WMSYS')
          AND partitioning_type = 'RANGE'
    """

    SQL_HIGH_VALUE = """
        DECLARE
            v_high_value VARCHAR2(4000);
        BEGIN
            SELECT high_value INTO v_high_value
            FROM (
                SELECT high_value 
                FROM dba_tab_partitions 
                WHERE table_owner = :owner AND table_name = :table_name
                ORDER BY partition_position DESC
            ) WHERE ROWNUM = 1;
            :out_bv := v_high_value;
        EXCEPTION WHEN OTHERS THEN
            :out_bv := NULL;
        END;
    """

    def __init__(self, config: ConnectionConfig, months_ahead: int = 2):
        self.config = config
        self.months_ahead = months_ahead
        self.target_date = datetime.now() + timedelta(days=30 * months_ahead)
        self.connection: Optional[cx_Oracle.Connection] = None

    def connect(self) -> bool:
        """Estabelece conexão."""
        try:
            self.connection = cx_Oracle.connect(
                user=self.config.user,
                password=self.config.password,
                dsn=self.config.dsn
            )
            return True
        except cx_Oracle.Error as e:
            logging.error(f"Conexão falhou: {e}")
            return False

    def get_partitioned_tables(self) -> List[Tuple[str, str, Optional[str]]]:
        """Lista tabelas RANGE particionadas."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(self.SQL_TABLES)
            return cursor.fetchall()
        finally:
            cursor.close()

    def get_max_high_value(self, owner: str, table_name: str) -> Optional[str]:
        """Extrai HIGH_VALUE da última partição."""
        cursor = self.connection.cursor()
        try:
            out_var = cursor.var(cx_Oracle.STRING)
            cursor.execute(
                self.SQL_HIGH_VALUE,
                owner=owner,
                table_name=table_name,
                out_bv=out_var
            )
            return out_var.getvalue()
        except cx_Oracle.Error:
            return None
        finally:
            cursor.close()

    @staticmethod
    def parse_high_value(high_value: str) -> Optional[datetime]:
        """Converte HIGH_VALUE para datetime."""
        if not high_value:
            return None
        try:
            date_str = high_value.split("'")[1].strip()
            fmt = "%Y-%m-%d %H:%M:%S" if len(date_str) > 10 else "%Y-%m-%d"
            return datetime.strptime(date_str, fmt)
        except (IndexError, ValueError):
            return None

    def check_table(self, owner: str, table_name: str, interval: Optional[str]) -> PartitionInfo:
        """Verifica uma tabela específica."""
        high_value = self.get_max_high_value(owner, table_name)
        high_date = self.parse_high_value(high_value)
        
        days_ahead = (high_date - datetime.now()).days if high_date else -999
        
        return PartitionInfo(
            owner=owner,
            table_name=table_name,
            high_value_date=high_date,
            is_interval=interval is not None,
            days_ahead=days_ahead
        )

    def run(self) -> Tuple[List[PartitionInfo], List[PartitionInfo]]:
        """Executa verificação. Retorna (ok, critical)."""
        if not self.connect():
            return [], []

        tables = self.get_partitioned_tables()
        ok_tables: List[PartitionInfo] = []
        critical_tables: List[PartitionInfo] = []

        logging.info(f"Verificando {len(tables)} tabelas particionadas...")
        logging.info(f"Data alvo: {self.target_date.strftime('%Y-%m-%d')}")

        for owner, table_name, interval in tables:
            info = self.check_table(owner, table_name, interval)
            
            if info.high_value_date is None:
                logging.warning(f"[SKIP] {owner}.{table_name} - HIGH_VALUE não legível")
                continue

            if info.high_value_date < self.target_date:
                critical_tables.append(info)
                logging.error(
                    f"[CRITICAL] {owner}.{table_name} - "
                    f"Max: {info.high_value_date.date()} ({info.days_ahead}d)"
                )
            else:
                ok_tables.append(info)
                logging.info(
                    f"[OK] {owner}.{table_name} - "
                    f"Max: {info.high_value_date.date()} ({info.days_ahead}d)"
                )

        return ok_tables, critical_tables


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


# Setup de Path para importar módulos irmãos
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from automacao.utils.connection import ConnectionConfig
    from automacao.utils.credentials import get_credentials
except ImportError:
    # Fallback
    class ConnectionConfig:
        def __init__(self, dsn, username, password, encoding="UTF-8"):
            self.dsn = dsn
            self.username = username  # Note: usando username para consistencia
            self.password = password
        @classmethod
        def from_cli(cls, cli_dsn=None, cli_user=None, cli_password=None):
            return cls(cli_dsn or 'localhost/orcl', cli_user or 'sys', cli_password or 'oracle')
    
    def get_credentials(cli_user, cli_password, cli_dsn):
        from collections import namedtuple
        Creds = namedtuple('DBCredentials', ['username', 'password', 'dsn'])
        return Creds(cli_user or 'sys', cli_password or 'oracle', cli_dsn or 'localhost/orcl')

def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="ORAEX - Partition Checker"
    )
    parser.add_argument("--dsn", help="host:port/service (Default: env ORACLE_DSN)")
    parser.add_argument("--user", help="DB user (Default: env ORACLE_USER)")
    parser.add_argument("--password", help="DB password (Default: env ORACLE_PASSWORD)")
    parser.add_argument("--months-ahead", type=int, default=2, help="Meses à frente")

    args = parser.parse_args()
    setup_logging()

    creds = get_credentials(args.user, args.password, args.dsn)

    if not creds.dsn or not creds.username or not creds.password:
         logging.error("Credenciais insuficientes. Configure ORACLE_USER/PASSWORD/DSN ou use argumentos CLI.")
         return 1

    config = ConnectionConfig(
        dsn=creds.dsn,
        user=creds.username,
        password=creds.password
    )

    checker = PartitionChecker(config, args.months_ahead)
    ok_tables, critical_tables = checker.run()

    if critical_tables:
        logging.error(f"FALHA: {len(critical_tables)} tabela(s) precisam de partições.")
        return 2
    
    logging.info(f"SUCESSO: {len(ok_tables)} tabela(s) OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
