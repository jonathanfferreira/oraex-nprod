"""
ORAEX - Oracle Prometheus Exporter
----------------------------------
Expõe métricas do Oracle Database em formato Prometheus.
Coleta métricas de tablespaces, sessões, performance, etc.

Uso:
    python oracle_exporter.py --port 9161 --dsn localhost/orcl
    
Métricas expostas em: http://localhost:9161/metrics
"""
import os
import sys
import time
import logging
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, List, Optional
from dataclasses import dataclass

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    import cx_Oracle
except ImportError:
    cx_Oracle = None

try:
    from automacao.utils.connection import ConnectionConfig
except ImportError:
    ConnectionConfig = None


@dataclass
class Metric:
    """Representa uma métrica Prometheus."""
    name: str
    value: float
    labels: Dict[str, str]
    metric_type: str = "gauge"
    help_text: str = ""


class OracleCollector:
    """Coleta métricas do Oracle Database."""
    
    # Queries para coleta de métricas
    QUERIES = {
        "tablespace_usage": """
            SELECT 
                t.tablespace_name,
                ROUND((t.bytes - NVL(f.bytes, 0)) / t.bytes * 100, 2) as pct_used,
                ROUND(t.bytes / 1024 / 1024, 2) as total_mb,
                ROUND(NVL(f.bytes, 0) / 1024 / 1024, 2) as free_mb
            FROM 
                (SELECT tablespace_name, SUM(bytes) as bytes FROM dba_data_files GROUP BY tablespace_name) t
            LEFT JOIN 
                (SELECT tablespace_name, SUM(bytes) as bytes FROM dba_free_space GROUP BY tablespace_name) f
            ON t.tablespace_name = f.tablespace_name
        """,
        "session_count": """
            SELECT 
                status,
                COUNT(*) as cnt
            FROM v$session
            WHERE type = 'USER'
            GROUP BY status
        """,
        "database_status": """
            SELECT 
                name,
                open_mode,
                database_role,
                force_logging
            FROM v$database
        """,
        "instance_status": """
            SELECT 
                instance_name,
                status,
                ROUND((SYSDATE - startup_time) * 24 * 60, 2) as uptime_minutes
            FROM v$instance
        """,
        "wait_events": """
            SELECT 
                wait_class,
                SUM(time_waited) as time_waited_secs,
                SUM(total_waits) as total_waits
            FROM v$system_wait_class
            WHERE wait_class != 'Idle'
            GROUP BY wait_class
        """,
        "sga_usage": """
            SELECT 
                name,
                ROUND(bytes / 1024 / 1024, 2) as size_mb
            FROM v$sgainfo
            WHERE name IN ('Total SGA Size', 'Free SGA Memory Available')
        """,
        "fra_usage": """
            SELECT
                name,
                ROUND(space_limit / 1024 / 1024, 2) as limit_mb,
                ROUND(space_used / 1024 / 1024, 2) as used_mb,
                ROUND(space_used / space_limit * 100, 2) as pct_used
            FROM v$recovery_file_dest
        """,
        "blocking_sessions": """
            SELECT
                COUNT(*) as blocking_count,
                NVL(MAX(seconds_in_wait), 0) as max_wait_seconds
            FROM v$session
            WHERE blocking_session IS NOT NULL
        """,
        "asm_diskgroups": """
            SELECT
                name,
                ROUND(total_mb / 1024, 2) as total_gb,
                ROUND(free_mb / 1024, 2) as free_gb,
                ROUND((total_mb - free_mb) / total_mb * 100, 2) as pct_used
            FROM v$asm_diskgroup
        """,
        "pga_usage": """
            SELECT
                ROUND(value / 1024 / 1024, 2) as mb
            FROM v$pgastat
            WHERE name = 'total PGA allocated'
        """,
        "redo_switches": """
            SELECT COUNT(*) as switches
            FROM v$log_history
            WHERE first_time > SYSDATE - 1/24
        """,
        "archiver_status": """
            SELECT
                CASE WHEN status = 'STARTED' THEN 1 ELSE 0 END as is_running
            FROM v$instance
            WHERE archiver != 'STOPPED'
        """
    }
    
    def __init__(self, config: "ConnectionConfig"):
        self.config = config
        self.connection: Optional[cx_Oracle.Connection] = None
        self.logger = logging.getLogger("OracleCollector")
    
    def connect(self, retries: int = 3, delay: int = 5) -> bool:
        """Estabelece conexão com o banco, com retry."""
        for attempt in range(1, retries + 1):
            try:
                self.connection = cx_Oracle.connect(
                    user=self.config.username,
                    password=self.config.password,
                    dsn=self.config.dsn
                )
                self.logger.info(f"Conectado a {self.config.dsn}")
                return True
            except Exception as e:
                self.logger.warning(f"Tentativa {attempt}/{retries} falhou: {e}")
                if attempt < retries:
                    time.sleep(delay)
                self.connection = None
        self.logger.error(f"Falha ao conectar apos {retries} tentativas")
        return False
    
    def collect(self) -> List[Metric]:
        """Coleta todas as métricas."""
        metrics = []
        
        if not self.connection:
            if not self.connect():
                metrics.append(Metric(
                    name="oracle_up",
                    value=0,
                    labels={"dsn": self.config.dsn},
                    help_text="Database is up"
                ))
                return metrics
        
        # Database UP
        metrics.append(Metric(
            name="oracle_up",
            value=1,
            labels={"dsn": self.config.dsn},
            help_text="Database is up"
        ))
        
        # Coletar cada tipo de métrica
        metrics.extend(self._collect_tablespace())
        metrics.extend(self._collect_sessions())
        metrics.extend(self._collect_blocking_sessions())
        metrics.extend(self._collect_instance())
        metrics.extend(self._collect_waits())
        metrics.extend(self._collect_sga())
        metrics.extend(self._collect_fra())
        metrics.extend(self._collect_asm())
        metrics.extend(self._collect_redo())
        
        return metrics
    
    def _execute_query(self, query: str) -> List[tuple]:
        """Executa query e retorna resultados."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            self.logger.warning(f"Erro na query: {e}")
            return []
    
    def _collect_tablespace(self) -> List[Metric]:
        """Coleta métricas de tablespaces."""
        metrics = []
        for row in self._execute_query(self.QUERIES["tablespace_usage"]):
            ts_name, pct_used, total_mb, free_mb = row
            metrics.append(Metric(
                name="oracle_tablespace_used_percent",
                value=pct_used,
                labels={"tablespace": ts_name},
                help_text="Tablespace usage percentage"
            ))
            metrics.append(Metric(
                name="oracle_tablespace_size_mb",
                value=total_mb,
                labels={"tablespace": ts_name},
                help_text="Tablespace total size in MB"
            ))
            metrics.append(Metric(
                name="oracle_tablespace_free_mb",
                value=free_mb,
                labels={"tablespace": ts_name},
                help_text="Tablespace free space in MB"
            ))
        return metrics
    
    def _collect_sessions(self) -> List[Metric]:
        """Coleta métricas de sessões."""
        metrics = []
        total = 0
        for row in self._execute_query(self.QUERIES["session_count"]):
            status, count = row
            total += count
            metrics.append(Metric(
                name="oracle_sessions_count",
                value=count,
                labels={"status": status.lower()},
                help_text="Number of user sessions by status"
            ))
        metrics.append(Metric(
            name="oracle_sessions_total",
            value=total,
            labels={},
            help_text="Total number of user sessions"
        ))
        return metrics
    
    def _collect_instance(self) -> List[Metric]:
        """Coleta métricas da instância."""
        metrics = []
        for row in self._execute_query(self.QUERIES["instance_status"]):
            instance_name, status, uptime_minutes = row
            metrics.append(Metric(
                name="oracle_instance_uptime_minutes",
                value=uptime_minutes,
                labels={"instance": instance_name},
                help_text="Instance uptime in minutes"
            ))
            metrics.append(Metric(
                name="oracle_instance_status",
                value=1 if status == "OPEN" else 0,
                labels={"instance": instance_name, "status": status},
                help_text="Instance status (1=OPEN)"
            ))
        return metrics
    
    def _collect_waits(self) -> List[Metric]:
        """Coleta métricas de wait events."""
        metrics = []
        for row in self._execute_query(self.QUERIES["wait_events"]):
            wait_class, time_waited, total_waits = row
            metrics.append(Metric(
                name="oracle_wait_time_seconds",
                value=time_waited / 100,  # centiseconds to seconds
                labels={"wait_class": wait_class.lower().replace(" ", "_")},
                metric_type="counter",
                help_text="Total wait time in seconds"
            ))
            metrics.append(Metric(
                name="oracle_wait_count",
                value=total_waits,
                labels={"wait_class": wait_class.lower().replace(" ", "_")},
                metric_type="counter",
                help_text="Total wait count"
            ))
        return metrics
    
    def _collect_sga(self) -> List[Metric]:
        """Coleta métricas de SGA."""
        metrics = []
        name_map = {
            "Total SGA Size": "oracle_sga_total_mb",
            "Free SGA Memory Available": "oracle_sga_free_mb",
        }
        for row in self._execute_query(self.QUERIES["sga_usage"]):
            name, size_mb = row
            metric_name = name_map.get(name, "oracle_sga_" + name.lower().replace(" ", "_") + "_mb")
            metrics.append(Metric(
                name=metric_name,
                value=size_mb,
                labels={},
                help_text=f"SGA {name} in MB"
            ))
        return metrics

    def _collect_blocking_sessions(self) -> List[Metric]:
        """Coleta métricas de sessões bloqueantes."""
        metrics = []
        for row in self._execute_query(self.QUERIES["blocking_sessions"]):
            count, max_wait = row
            metrics.append(Metric(
                name="oracle_blocking_sessions_count",
                value=count,
                labels={},
                help_text="Number of blocking sessions"
            ))
            metrics.append(Metric(
                name="oracle_blocking_sessions_max_wait_seconds",
                value=max_wait,
                labels={},
                help_text="Max wait time of blocked sessions in seconds"
            ))
        return metrics

    def _collect_asm(self) -> List[Metric]:
        """Coleta métricas de ASM diskgroups."""
        metrics = []
        for row in self._execute_query(self.QUERIES["asm_diskgroups"]):
            name, total_gb, free_gb, pct_used = row
            metrics.append(Metric(
                name="oracle_asm_diskgroup_free_gb",
                value=free_gb,
                labels={"diskgroup": name},
                help_text="ASM diskgroup free space in GB"
            ))
            metrics.append(Metric(
                name="oracle_asm_diskgroup_used_percent",
                value=pct_used,
                labels={"diskgroup": name},
                help_text="ASM diskgroup usage percentage"
            ))
        return metrics

    def _collect_redo(self) -> List[Metric]:
        """Coleta métricas de redo log switches."""
        metrics = []
        for row in self._execute_query(self.QUERIES["redo_switches"]):
            switches = row[0]
            metrics.append(Metric(
                name="oracle_redo_log_switches_total",
                value=switches,
                labels={},
                metric_type="counter",
                help_text="Redo log switches in last hour"
            ))
        return metrics
    
    def _collect_fra(self) -> List[Metric]:
        """Coleta métricas de FRA."""
        metrics = []
        for row in self._execute_query(self.QUERIES["fra_usage"]):
            name, limit_mb, used_mb, pct_used = row
            metrics.append(Metric(
                name="oracle_fra_limit_mb",
                value=limit_mb,
                labels={},
                help_text="FRA size limit in MB"
            ))
            metrics.append(Metric(
                name="oracle_fra_used_mb",
                value=used_mb,
                labels={},
                help_text="FRA used space in MB"
            ))
            metrics.append(Metric(
                name="oracle_fra_used_percent",
                value=pct_used,
                labels={},
                help_text="FRA usage percentage"
            ))
        return metrics


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP Handler para servir métricas no formato Prometheus."""
    
    collector: OracleCollector = None
    
    def do_GET(self):
        if self.path == "/metrics":
            self._serve_metrics()
        elif self.path == "/health":
            self._serve_health()
        else:
            self.send_response(404)
            self.end_headers()
    
    def _serve_metrics(self):
        """Serve métricas no formato Prometheus."""
        metrics = self.collector.collect()
        
        output = []
        seen_help = set()
        
        for metric in metrics:
            # HELP e TYPE (apenas uma vez por métrica)
            if metric.name not in seen_help:
                output.append(f"# HELP {metric.name} {metric.help_text}")
                output.append(f"# TYPE {metric.name} {metric.metric_type}")
                seen_help.add(metric.name)
            
            # Valor com labels
            if metric.labels:
                labels_str = ",".join(f'{k}="{v}"' for k, v in metric.labels.items())
                output.append(f"{metric.name}{{{labels_str}}} {metric.value}")
            else:
                output.append(f"{metric.name} {metric.value}")
        
        content = "\n".join(output) + "\n"
        
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode())
    
    def _serve_health(self):
        """Endpoint de health check."""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")
    
    def log_message(self, format, *args):
        """Silencia logs de request."""
        pass


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description="Oracle Prometheus Exporter")
    parser.add_argument("--port", type=int, default=9161, help="Port to listen on (default: 9161)")
    parser.add_argument("--dsn", help="DSN (Default: env ORACLE_DSN)")
    parser.add_argument("--user", help="User (Default: env ORACLE_USER)")
    parser.add_argument("--password", help="Password (Default: env ORACLE_PASSWORD)")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    if cx_Oracle is None:
        logging.error("cx_Oracle não instalado. Execute: pip install cx_Oracle")
        return 1
    
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
    
    # Criar collector e injetar no handler
    collector = OracleCollector(config)
    MetricsHandler.collector = collector
    
    # Iniciar servidor
    server = HTTPServer(("0.0.0.0", args.port), MetricsHandler)
    logging.info(f"Oracle Exporter iniciado em http://0.0.0.0:{args.port}/metrics")
    logging.info(f"DSN: {config.dsn}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        server.shutdown()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
