#!/usr/bin/env python3
"""
Script de Análise de Índices MongoDB (Performance Tuning).
Identifica índices não utilizados (0 Ops) que consomem memória e disco desnecessariamente.
"""
import sys
import os
import argparse
import logging
import json

# Setup path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

try:
    from automacao.utils.logging_config import setup_logging
    import pymongo
except ImportError:
    sys.exit(1)

def analyze_indexes(uri: str):
    """Percorre DBs e Collections buscando índices não usados."""
    try:
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        dbs = client.list_database_names()
        
        system_dbs = ['admin', 'local', 'config']
        total_unused = 0
        
        logging.info("🔍 Iniciando Análise de Índices...")
        
        for db_name in dbs:
            if db_name in system_dbs:
                continue
                
            db = client[db_name]
            colls = db.list_collection_names()
            
            for coll_name in colls:
                coll = db[coll_name]
                try:
                    # Pipeline $indexStats retorna estatísticas de uso
                    stats = list(coll.aggregate([{"$indexStats": {}}]))
                    
                    for stat in stats:
                        index_name = stat.get("name")
                        accesses = stat.get("accesses", {})
                        ops = accesses.get("ops", 0)
                        since = accesses.get("since")
                        
                        # Ignora índice padrão _id_
                        if index_name == "_id_":
                            continue
                            
                        if ops == 0:
                            logging.warning(f"⚠️ UNUSED INDEX: {db_name}.{coll_name} -> {index_name} (0 ops since {since})")
                            total_unused += 1
                        else:
                            logging.info(f"✅ Active Index: {db_name}.{coll_name} -> {index_name} ({ops} ops)")
                            
                except Exception as e:
                    logging.error(f"Erro ao analisar {db_name}.{coll_name}: {e}")

        if total_unused == 0:
            logging.info("🎉 Nenhum índice inútil encontrado! Ótimo trabalho.")
            return True
        else:
            logging.warning(f"📉 Total de Índices Não Usados: {total_unused}. Considere removê-los.")
            return False

    except Exception as e:
        logging.error(f"Falha na análise: {e}")
        return False
    finally:
        client.close()

def main():
    parser = argparse.ArgumentParser(description="MongoDB Index Analyzer")
    parser.add_argument("--uri", help="Mongo URI")
    parser.add_argument("--json", action="store_true", help="JSON Logs")
    
    args = parser.parse_args()
    setup_logging(json_mode=args.json)
    
    uri = args.uri or os.environ.get("MONGO_URI")
    if not uri:
        logging.error("Defina MONGO_URI")
        sys.exit(1)

    analyze_indexes(uri)

if __name__ == "__main__":
    main()
