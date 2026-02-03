#!/usr/bin/env python3
"""
Script de Monitoramento de Oplog e Replication Lag (MongoDB).
- Verifica o atraso (Lag) de replicação dos Secondaries.
- Calcula a janela de tempo do Oplog (Oplog Window).
"""
import sys
import os
import argparse
import logging
from datetime import datetime
import time

# Setup path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

try:
    from automacao.utils.logging_config import setup_logging
    import pymongo
except ImportError:
    sys.exit(1)

def get_oplog_window(client) -> float:
    """Retorna janela do Oplog em horas."""
    try:
        # Pega timestamp do primeiro e último registro do oplog
        oplog = client.local.oplog.rs
        first = oplog.find_one(sort=[('$natural', 1)])
        last = oplog.find_one(sort=[('$natural', -1)])
        
        if not first or not last:
            return 0.0
            
        t1 = first['ts'].time
        t2 = last['ts'].time
        
        diff_hours = (t2 - t1) / 3600.0
        return round(diff_hours, 2)
    except Exception as e:
        logging.error(f"Erro ao calcular Oplog Window: {e}")
        return 0.0

def check_lag_and_oplog(uri: str, lag_threshold_sec: int, min_oplog_hours: int) -> bool:
    """Verifica Lag e Oplog."""
    try:
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        status = client.admin.command("replSetGetStatus")
        
        primary_optime = None
        members = status.get("members", [])
        
        # 1. Identificar Primary Optime
        for m in members:
            if m.get("stateStr") == "PRIMARY":
                primary_optime = m.get("optimeDate")
                break
        
        if not primary_optime:
            logging.critical("🚨 Primary não encontrado! Impossível calcular lag.")
            return False

        all_ok = True
        
        # 2. Verificar Lag dos Secondaries
        logging.info(f"Primary Optime: {primary_optime}")
        for m in members:
            name = m.get("name")
            state = m.get("stateStr")
            
            if state == "SECONDARY":
                sec_optime = m.get("optimeDate")
                lag = (primary_optime - sec_optime).total_seconds()
                
                msg = f"{name} Lag: {lag:.2f}s"
                if lag > lag_threshold_sec:
                    logging.warning(f"⚠️ HIGH LAG: {msg} (Threshold: {lag_threshold_sec}s)")
                    all_ok = False
                else:
                    logging.info(f"✅ {msg}")

        # 3. Verificar Oplog Window
        window_hours = get_oplog_window(client)
        msg_oplog = f"Oplog Window: {window_hours}h"
        
        if window_hours < min_oplog_hours:
            logging.warning(f"⚠️ SHORT OPLOG: {msg_oplog} (Min: {min_oplog_hours}h)")
            all_ok = False
        else:
            logging.info(f"✅ {msg_oplog}")

        client.close()
        return all_ok

    except Exception as e:
        logging.error(f"Falha na checagem: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Monitoramento Oplog & Lag MongoDB")
    parser.add_argument("--uri", help="Mongo URI (Default: env MONGO_URI)")
    parser.add_argument("--lag-max", type=int, default=10, help="Max lag seconds (Default: 10)")
    parser.add_argument("--oplog-min", type=int, default=24, help="Min oplog hours (Default: 24)")
    parser.add_argument("--json", action="store_true", help="JSON Logs")
    
    args = parser.parse_args()
    setup_logging(json_mode=args.json)
    
    uri = args.uri or os.environ.get("MONGO_URI")
    if not uri:
        logging.error("Defina MONGO_URI")
        sys.exit(1)

    if not check_lag_and_oplog(uri, args.lag_max, args.oplog_min):
        sys.exit(1)

if __name__ == "__main__":
    main()
