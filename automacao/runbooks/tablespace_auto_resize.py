"""
Tablespace Auto-Resize Runbook
------------------------------
Detecta tablespaces com uso > threshold e executa resize automático.
Segue padrão BOOK DBA Getnet para manutenção proativa.

Uso:
    python -m automacao.runbooks.tablespace_auto_resize --dsn localhost/orcl
"""
import logging
import os
import sys
from typing import List, Optional, Dict

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


class TablespaceAutoResize(BaseRunbook):
    """
    Runbook para auto-resize de tablespaces.
    
    Fluxo:
    1. Detecta tablespaces acima do threshold
    2. Para cada uma, tenta adicionar datafile ou resize
    3. Valida se o espaço foi liberado
    4. Notifica resultado
    """
    
    SQL_CHECK_TABLESPACES = """
        SELECT 
            t.tablespace_name,
            ROUND((t.bytes - NVL(f.bytes, 0)) / t.bytes * 100, 2) as pct_used,
            ROUND(t.bytes / 1024 / 1024, 2) as total_mb,
            ROUND(NVL(f.bytes, 0) / 1024 / 1024, 2) as free_mb,
            (SELECT file_name FROM dba_data_files df 
             WHERE df.tablespace_name = t.tablespace_name AND ROWNUM = 1) as sample_file
        FROM 
            (SELECT tablespace_name, SUM(bytes) as bytes FROM dba_data_files GROUP BY tablespace_name) t
        LEFT JOIN 
            (SELECT tablespace_name, SUM(bytes) as bytes FROM dba_free_space GROUP BY tablespace_name) f
        ON t.tablespace_name = f.tablespace_name
        WHERE ROUND((t.bytes - NVL(f.bytes, 0)) / t.bytes * 100, 2) >= :threshold
        ORDER BY 2 DESC
    """
    
    SQL_ADD_DATAFILE = """
        ALTER TABLESPACE {tablespace_name} 
        ADD DATAFILE '{new_file_path}' 
        SIZE {size_mb}M AUTOEXTEND ON NEXT 100M MAXSIZE 32G
    """
    
    def __init__(
        self, 
        config: "ConnectionConfig",
        threshold: int = 90,
        add_size_mb: int = 1024,
        dry_run: bool = False
    ):
        super().__init__(name="TablespaceAutoResize")
        self.config = config
        self.threshold = threshold
        self.add_size_mb = add_size_mb
        self.dry_run = dry_run
        self.connection: Optional[cx_Oracle.Connection] = None
        self.critical_tablespaces: List[Dict] = []
        self.remediated: List[str] = []
    
    def validate_preconditions(self) -> bool:
        """Valida conexão e permissões."""
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
            
            # Verificar permissão DBA
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1 FROM dba_tablespaces WHERE ROWNUM = 1")
            cursor.close()
            self.log_step("Permissões DBA verificadas")
            
            return True
            
        except cx_Oracle.Error as e:
            self.errors.append(f"Erro de conexão: {e}")
            return False
    
    def execute(self) -> bool:
        """Detecta e corrige tablespaces cheias."""
        self.log_step(f"Verificando tablespaces > {self.threshold}%")
        
        cursor = self.connection.cursor()
        cursor.execute(self.SQL_CHECK_TABLESPACES, threshold=self.threshold)
        
        for row in cursor.fetchall():
            ts_name, pct_used, total_mb, free_mb, sample_file = row
            
            self.critical_tablespaces.append({
                "name": ts_name,
                "pct_used": pct_used,
                "total_mb": total_mb,
                "free_mb": free_mb
            })
            
            self.logger.warning(
                f"[CRITICAL] {ts_name}: {pct_used}% usado "
                f"({total_mb - free_mb:.0f}MB / {total_mb:.0f}MB)"
            )
            
            if self.dry_run:
                self.log_step(f"[DRY-RUN] Pulando resize de {ts_name}")
                continue
            
            # Tentar adicionar datafile
            if self._add_datafile(ts_name, sample_file):
                self.remediated.append(ts_name)
                self.log_step(f"Datafile adicionado: {ts_name}")
            else:
                self.log_step(f"Falha ao adicionar datafile: {ts_name}", success=False)
        
        cursor.close()
        
        if not self.critical_tablespaces:
            self.log_step(f"Nenhuma tablespace acima de {self.threshold}%")
        
        return True  # Sempre retorna True, falhas individuais são logadas
    
    def _add_datafile(self, ts_name: str, sample_file: str) -> bool:
        """Adiciona novo datafile à tablespace."""
        try:
            # Gerar nome do novo arquivo baseado no existente
            if sample_file:
                import re
                # Incrementar número no nome do arquivo
                match = re.search(r'(\d+)(\.dbf)$', sample_file)
                if match:
                    num = int(match.group(1)) + 1
                    new_file = re.sub(r'\d+(\.dbf)$', f'{num:02d}\\1', sample_file)
                else:
                    new_file = sample_file.replace('.dbf', '_02.dbf')
            else:
                new_file = f'/u02/oracle/oradata/{ts_name.lower()}_01.dbf'
            
            sql = self.SQL_ADD_DATAFILE.format(
                tablespace_name=ts_name,
                new_file_path=new_file,
                size_mb=self.add_size_mb
            )
            
            self.logger.info(f"Executando: {sql}")
            cursor = self.connection.cursor()
            cursor.execute(sql)
            cursor.close()
            
            send_alert(
                "OK",
                f"Tablespace {ts_name} expandida automaticamente",
                {"new_file": new_file, "size_mb": self.add_size_mb}
            )
            
            return True
            
        except cx_Oracle.Error as e:
            self.logger.error(f"Erro ao adicionar datafile: {e}")
            send_alert(
                "WARNING",
                f"Falha ao expandir tablespace {ts_name}",
                {"error": str(e)}
            )
            return False
    
    def validate_postconditions(self) -> bool:
        """Valida que o espaço foi liberado."""
        if self.dry_run or not self.remediated:
            return True
        
        self.log_step("Validando pós-condições")
        
        cursor = self.connection.cursor()
        for ts_name in self.remediated:
            cursor.execute("""
                SELECT ROUND((t.bytes - NVL(f.bytes, 0)) / t.bytes * 100, 2)
                FROM (SELECT tablespace_name, SUM(bytes) as bytes FROM dba_data_files 
                      WHERE tablespace_name = :ts GROUP BY tablespace_name) t
                LEFT JOIN (SELECT tablespace_name, SUM(bytes) as bytes FROM dba_free_space 
                           WHERE tablespace_name = :ts GROUP BY tablespace_name) f
                ON t.tablespace_name = f.tablespace_name
            """, ts=ts_name)
            
            row = cursor.fetchone()
            if row and row[0] < self.threshold:
                self.log_step(f"{ts_name} agora em {row[0]}%")
            else:
                self.log_step(f"{ts_name} ainda acima do threshold", success=False)
        
        cursor.close()
        return True
    
    def rollback(self) -> bool:
        """Rollback não aplicável para adição de datafiles."""
        self.log_step("Rollback não necessário (adição de datafiles é segura)")
        return True


def main():
    """Entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Tablespace Auto-Resize Runbook")
    parser.add_argument("--dsn", help="DSN (Default: env ORACLE_DSN)")
    parser.add_argument("--user", help="User (Default: env ORACLE_USER)")
    parser.add_argument("--password", help="Password (Default: env ORACLE_PASSWORD)")
    parser.add_argument("--threshold", type=int, default=90, help="% threshold (default: 90)")
    parser.add_argument("--add-size", type=int, default=1024, help="MB a adicionar (default: 1024)")
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
    
    runbook = TablespaceAutoResize(
        config=config,
        threshold=args.threshold,
        add_size_mb=args.add_size,
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
