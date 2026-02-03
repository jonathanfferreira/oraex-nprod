#!/usr/bin/env python3
"""
MongoDB Unified Health Check (Enterprise Grade).
Consolida múltiplas verificações em um único relatório para DBREs.
Checklist:
1. Conectividade (Ping)
2. Replica Set Health (Split-brain check)
3. Oplog Window & Lag
4. Connections (Available vs Current)
5. Profiling Level (Performance Impact)
"""
import sys
import os
import argparse
import logging
import json
from datetime import datetime

# Setup path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

try:
    from automacao.utils.logging_config import setup_logging
    from automacao.mongodb.monitoramento.check_replica_set import check_replica_set
    from automacao.mongodb.monitoramento.check_oplog_lag import check_lag_and_oplog
    import pymongo
except ImportError as e:
    print(f"Erro de Importacao: {e}")
    sys.exit(1)

def check_connections(client) -> dict:
    """Verifica % de conexões em uso."""
    try:
        server_status = client.admin.command("serverStatus")
        conns = server_status.get("connections", {})
        current = conns.get("current", 0)
        available = conns.get("available", 1)
        total = current + available
        
        pct_used = (current / total) * 100 if total > 0 else 0
        
        status = "OK"
        if pct_used > 80:
            status = "CRITICAL"
            logging.error(f"🚨 High Connection Usage: {pct_used:.2f}% ({current}/{total})")
        elif pct_used > 60:
            status = "WARNING"
            logging.warning(f"⚠️ Elevated Connection Usage: {pct_used:.2f}%")
        else:
            logging.info(f"✅ Connections: {pct_used:.2f}% ({current}/{total})")
            
        return {"current": current, "available": available, "pct_used": pct_used, "status": status}
    except Exception as e:
        logging.error(f"Connection check failed: {e}")
        return {"status": "ERROR", "error": str(e)}

def check_profiling(client) -> dict:
    """Verifica nível de profiling (Impacto em performance)."""
    try:
        # Check profiling level on 'oraex_db' or 'admin'
        # Em mongo, profiling é por DB. Vamos checar um db padrão ou iterar.
        # Simplificação: Checar se não está ALL (2) em excesso.
        db = client.get_database("admin")
        profile_level = db.command("profile", -1).get("was", 0)
        slowms = db.command("profile", -1).get("slowms", 100)
        
        status = "OK"
        msg = f"Profiling Level: {profile_level} (SlowMS: {slowms})"
        
        if profile_level == 2:
            status = "WARNING"
            logging.warning(f"⚠️ {msg} - Profiling ALL pode degradar performance!")
        else:
            logging.info(f"✅ {msg}")
            
        return {"level": profile_level, "slowms": slowms, "status": status}
    except Exception as e:
        # Profiling pode exigir privilegios
        return {"status": "SKIPPED", "error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="MongoDB Consolidated Health Check")
    parser.add_argument("--uri", help="Mongo URI (Default: env MONGO_URI)")
    parser.add_argument("--json", action="store_true", help="JSON Logs")
    
    args = parser.parse_args()
    setup_logging(json_mode=args.json)
    
    mongo_uri = args.uri or os.environ.get("MONGO_URI")
    if not mongo_uri:
        logging.error("Defina MONGO_URI")
        sys.exit(1)
        
    logging.info("🏥 Iniciando MongoDB Health Check Consolidado...")
    
    try:
        client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        logging.info("✅ Conectividade OK")
    except Exception as e:
        logging.critical(f"🔥 Falha crítica de conexão: {e}")
        sys.exit(1)

    # 1. Replica Set
    rs_ok = check_replica_set(client)
    
    # 2. Oplog & Lag (Requer URI para nova conexao interna ou refatorar para passar client)
    # O script original cria seu próprio client. Vamos executa-lo como função.
    # Nota: check_lag_and_oplog cria nova conexao internamente.
    # Em produção ideal refatoraríamos para injetar dependencia, mas para MVP ok.
    oplog_ok = check_lag_and_oplog(mongo_uri, 10, 24)
    
    # 3. Connections
    conn_data = check_connections(client)
    
    # 4. Profiling
    prof_data = check_profiling(client)
    
    # Summary
    overall_status = "OK" 
    if not rs_ok or not oplog_ok or conn_data.get("status") == "CRITICAL":
        overall_status = "CRITICAL"
    elif conn_data.get("status") == "WARNING" or prof_data.get("status") == "WARNING":
        overall_status = "WARNING"
        
    logging.info(f"🏁 Health Check Finalizado. Status Global: [{overall_status}]")
    
    # Em JSON mode, o logging ja estruturou. Se quisermos um output final consolidado:
    if args.json:
        # Apenas para facilitar leitura humana se redirecionado, mas os logs ja estao lá.
        pass

    client.close()
    if overall_status == "CRITICAL":
        sys.exit(2)
    elif overall_status == "WARNING":
        sys.exit(0) # Warning não quebra pipeline geralmente
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
