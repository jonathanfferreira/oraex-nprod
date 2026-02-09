#!/usr/bin/env python3
"""
ORAEX - SLO Tracker (Service Level Objectives)
-----------------------------------------------
Monitora e valida SLOs definidos para bancos de dados Oracle.
Aplicação de conceitos DBRE (Database Reliability Engineering).

Uso:
    python slo_tracker.py --dsn localhost:1521/orcl --slo availability:99.99
"""
import argparse
import logging
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from enum import Enum

import cx_Oracle

# Setup path para imports
sys.path.append('.')

try:
    from automacao.utils.logging_config import setup_logging
    from automacao.utils.credentials import get_credentials
except ImportError:
    # Fallback se não conseguir importar
    def setup_logging(*args, **kwargs):
        logging.basicConfig(level=logging.INFO)
    
    def get_credentials(**kwargs):
        from automacao.utils.credentials import DBCredentials
        return DBCredentials("system", "oracle", "localhost:1521/orcl")


class SLOStatus(Enum):
    """Status de um SLO"""
    MET = "MET"
    AT_RISK = "AT_RISK"  # Próximo de violar
    VIOLATED = "VIOLATED"
    UNKNOWN = "UNKNOWN"


class SLOTracker:
    """Tracker de Service Level Objectives"""
    
    # SLOs padrão (podem ser sobrescritos via argumentos)
    DEFAULT_SLOs = {
        "availability": 99.95,      # 99.95% uptime
        "rpo": 3600,                # 1 hora (segundos)
        "rto": 1800,                # 30 minutos (segundos)
        "query_latency_p95": 0.1,   # 100ms
        "connection_pool": 80.0,    # 80% máximo
    }
    
    def __init__(self, connection: cx_Oracle.Connection):
        self.connection = connection
        self.slos = self.DEFAULT_SLOs.copy()
        self.results = {}
    
    def set_slo(self, name: str, value: float):
        """Define um SLO customizado"""
        self.slos[name] = value
        logging.info(f"SLO '{name}' definido como {value}")
    
    def check_availability(self) -> Dict:
        """Verifica disponibilidade do banco"""
        try:
            # Query simples para verificar se está respondendo
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.fetchone()
            cursor.close()
            
            # Se chegou aqui, está disponível
            # Em produção, consultar métricas históricas de uptime
            uptime_percent = 100.0  # Placeholder - em produção, calcular baseado em histórico
            
            target = self.slos.get("availability", 99.95)
            status = SLOStatus.MET if uptime_percent >= target else SLOStatus.VIOLATED
            
            result = {
                "slo_name": "availability",
                "target": target,
                "current": uptime_percent,
                "status": status.value,
                "message": f"Uptime: {uptime_percent}% (Target: {target}%)"
            }
            
            if status == SLOStatus.VIOLATED:
                logging.error(f"🚨 SLO VIOLADO: {result['message']}")
            else:
                logging.info(f"✅ SLO OK: {result['message']}")
            
            return result
            
        except Exception as e:
            logging.error(f"Erro ao verificar disponibilidade: {e}")
            return {
                "slo_name": "availability",
                "status": SLOStatus.UNKNOWN.value,
                "error": str(e)
            }
    
    def check_query_latency(self) -> Dict:
        """Verifica latência P95 de queries"""
        try:
            # Query para obter estatísticas de latência
            sql = """
                SELECT 
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY elapsed_time) as p95_ms
                FROM v$sql 
                WHERE executions > 0 
                AND last_active_time > SYSDATE - 1/24  -- Última hora
            """
            
            cursor = self.connection.cursor()
            cursor.execute(sql)
            row = cursor.fetchone()
            cursor.close()
            
            if row and row[0]:
                p95_ms = row[0] / 1000  # Converter microsegundos para milissegundos
            else:
                p95_ms = 0.0
            
            target_ms = self.slos.get("query_latency_p95", 0.1) * 1000  # Converter para ms
            status = SLOStatus.MET if p95_ms <= target_ms else SLOStatus.VIOLATED
            
            result = {
                "slo_name": "query_latency_p95",
                "target_ms": target_ms,
                "current_ms": p95_ms,
                "status": status.value,
                "message": f"P95 Latency: {p95_ms:.2f}ms (Target: {target_ms:.2f}ms)"
            }
            
            if status == SLOStatus.VIOLATED:
                logging.warning(f"⚠️  SLO AT RISK: {result['message']}")
            else:
                logging.info(f"✅ SLO OK: {result['message']}")
            
            return result
            
        except Exception as e:
            logging.error(f"Erro ao verificar latência: {e}")
            return {
                "slo_name": "query_latency_p95",
                "status": SLOStatus.UNKNOWN.value,
                "error": str(e)
            }
    
    def check_connection_pool(self) -> Dict:
        """Verifica uso do connection pool"""
        try:
            sql = """
                SELECT 
                    (SELECT COUNT(*) FROM v$session WHERE status = 'ACTIVE') as active,
                    (SELECT VALUE FROM v$parameter WHERE name = 'processes') as max_processes
                FROM DUAL
            """
            
            cursor = self.connection.cursor()
            cursor.execute(sql)
            row = cursor.fetchone()
            cursor.close()
            
            active = row[0] if row else 0
            max_processes = row[1] if row else 100
            
            usage_percent = (active / max_processes) * 100 if max_processes > 0 else 0
            target = self.slos.get("connection_pool", 80.0)
            
            if usage_percent >= target:
                status = SLOStatus.VIOLATED
            elif usage_percent >= target * 0.8:  # 80% do target = at risk
                status = SLOStatus.AT_RISK
            else:
                status = SLOStatus.MET
            
            result = {
                "slo_name": "connection_pool",
                "target_percent": target,
                "current_percent": usage_percent,
                "active_connections": active,
                "max_connections": max_processes,
                "status": status.value,
                "message": f"Pool Usage: {usage_percent:.1f}% (Target: <{target}%)"
            }
            
            if status == SLOStatus.VIOLATED:
                logging.error(f"🚨 SLO VIOLADO: {result['message']}")
            elif status == SLOStatus.AT_RISK:
                logging.warning(f"⚠️  SLO AT RISK: {result['message']}")
            else:
                logging.info(f"✅ SLO OK: {result['message']}")
            
            return result
            
        except Exception as e:
            logging.error(f"Erro ao verificar connection pool: {e}")
            return {
                "slo_name": "connection_pool",
                "status": SLOStatus.UNKNOWN.value,
                "error": str(e)
            }
    
    def run_all_checks(self) -> Dict:
        """Executa todos os checks de SLO"""
        logging.info("Iniciando verificação de SLOs...")
        
        results = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "slos": [],
            "summary": {
                "total": 0,
                "met": 0,
                "at_risk": 0,
                "violated": 0,
                "unknown": 0
            }
        }
        
        # Executar checks
        checks = [
            self.check_availability(),
            self.check_query_latency(),
            self.check_connection_pool(),
        ]
        
        for check in checks:
            results["slos"].append(check)
            results["summary"]["total"] += 1
            
            status = check.get("status", "UNKNOWN")
            if status == SLOStatus.MET.value:
                results["summary"]["met"] += 1
            elif status == SLOStatus.AT_RISK.value:
                results["summary"]["at_risk"] += 1
            elif status == SLOStatus.VIOLATED.value:
                results["summary"]["violated"] += 1
            else:
                results["summary"]["unknown"] += 1
        
        # Status geral
        if results["summary"]["violated"] > 0:
            results["overall_status"] = "CRITICAL"
        elif results["summary"]["at_risk"] > 0:
            results["overall_status"] = "WARNING"
        else:
            results["overall_status"] = "OK"
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Tracker de SLOs para Oracle Database"
    )
    parser.add_argument("--user", help="Usuário Oracle")
    parser.add_argument("--password", help="Senha Oracle")
    parser.add_argument("--dsn", help="DSN Oracle (host:port/service)")
    parser.add_argument("--json", action="store_true", help="Output em JSON")
    parser.add_argument("--slo", action="append", help="SLO customizado (ex: availability:99.99)")
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(json_mode=args.json)
    
    # Obter credenciais
    creds = get_credentials(
        cli_user=args.user,
        cli_password=args.password,
        cli_dsn=args.dsn
    )
    
    # Conectar
    try:
        connection = cx_Oracle.connect(
            creds.username,
            creds.password,
            creds.dsn,
            encoding="UTF-8"
        )
        logging.info(f"Conectado ao banco: {creds.dsn}")
    except Exception as e:
        logging.error(f"Erro ao conectar: {e}")
        sys.exit(1)
    
    try:
        # Criar tracker
        tracker = SLOTracker(connection)
        
        # Configurar SLOs customizados
        if args.slo:
            for slo_def in args.slo:
                try:
                    name, value = slo_def.split(":")
                    tracker.set_slo(name, float(value))
                except ValueError:
                    logging.warning(f"SLO inválido ignorado: {slo_def}")
        
        # Executar checks
        results = tracker.run_all_checks()
        
        # Output
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print("\n" + "="*70)
            print("📊 RESUMO DE SLOs")
            print("="*70)
            print(f"Status Geral: {results['overall_status']}")
            print(f"✅ Met: {results['summary']['met']}")
            print(f"⚠️  At Risk: {results['summary']['at_risk']}")
            print(f"🚨 Violated: {results['summary']['violated']}")
            print(f"❓ Unknown: {results['summary']['unknown']}")
            print("\nDetalhes:")
            for slo in results["slos"]:
                status_icon = {
                    "MET": "✅",
                    "AT_RISK": "⚠️",
                    "VIOLATED": "🚨",
                    "UNKNOWN": "❓"
                }.get(slo.get("status"), "❓")
                print(f"  {status_icon} {slo.get('slo_name', 'unknown')}: {slo.get('message', 'N/A')}")
        
        # Exit code baseado no status
        if results["overall_status"] == "CRITICAL":
            sys.exit(2)
        elif results["overall_status"] == "WARNING":
            sys.exit(1)
        else:
            sys.exit(0)
            
    finally:
        connection.close()


if __name__ == "__main__":
    main()
