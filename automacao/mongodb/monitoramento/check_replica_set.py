#!/usr/bin/env python3
"""
Script de Monitoramento de Replica Set MongoDB.
Verifica o status dos membros (PRIMARY/SECONDARY) e saúde do cluster.
"""
import sys
import os
import argparse
import logging
from datetime import datetime

# Setup path para importar módulos da raiz (automacao.utils)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

try:
    from automacao.utils.logging_config import setup_logging
    import pymongo
    from pymongo.errors import ConnectionFailure, OperationFailure
except ImportError as e:
    print(f"Erro de importação: {e}")
    print("Instale dependencia: pip install pymongo")
    sys.exit(1)

def get_mongo_connection(uri: str):
    """Retorna cliente Mongo."""
    try:
        # ConnectTimeout curto para falhar rápido
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Força verificação da conexão
        client.admin.command('ping')
        return client
    except Exception as e:
        logging.error(f"Falha ao conectar no MongoDB: {e}")
        return None

def check_replica_set(client) -> bool:
    """
    Verifica status do Replica Set via comando 'replSetGetStatus'.
    Retorna True se saudável (Existe Primary e todos membros OK).
    """
    try:
        status = client.admin.command("replSetGetStatus")
        set_name = status.get("set", "Unknown")
        members = status.get("members", [])
        
        primary_count = 0
        healthy = True
        
        logging.info(f"Analisando ReplicaSet: {set_name} | Membros: {len(members)}")
        
        for member in members:
            name = member.get("name")
            state_str = member.get("stateStr")  # PRIMARY, SECONDARY, etc
            health = member.get("health")      # 1 = UP, 0 = DOWN
            
            if state_str == "PRIMARY":
                primary_count += 1
            
            msg = f"{name} -> [{state_str}] (Health: {health})"
            
            if health == 1:
                logging.info(msg)
            else:
                logging.error(f"❌ {msg}")
                healthy = False

        if primary_count == 0:
            logging.critical("🚨 NENHUM PRIMARY ENCONTRADO! Cluster pode estar em modo Read-Only ou caído.")
            healthy = False
        elif primary_count > 1:
            logging.warning(f"⚠️ Múltiplos PRIMARYs detectados ({primary_count}). Split-brain?")
            
        return healthy

    except OperationFailure as e:
        logging.error(f"Erro ao executar comando replSetGetStatus: {e}")
        # Pode ser que não seja um Replica Set (Standalone)
        if "not running with --replSet" in str(e):
            logging.warning("⚠️ Instância não roda como Replica Set.")
        return False
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Monitoramento MongoDB Replica Set")
    parser.add_argument("--uri", help="Connection URI (ex: mongodb://user:pass@host:27017). Default: env MONGO_URI")
    parser.add_argument("--json", action="store_true", help="Logs em JSON")
    
    args = parser.parse_args()
    
    setup_logging(json_mode=args.json)
    
    mongo_uri = args.uri or os.environ.get("MONGO_URI")
    if not mongo_uri:
        logging.error("URI não fornecida. Use --uri ou defina MONGO_URI.")
        sys.exit(1)
        
    client = get_mongo_connection(mongo_uri)
    if not client:
        sys.exit(1)
        
    success = check_replica_set(client)
    client.close()
    
    if not success:
        sys.exit(1) # Falha no monitoramento

if __name__ == "__main__":
    main()
