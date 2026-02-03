#!/usr/bin/env python3
"""
MongoDB Backup Manager (Wrapper para mongodump).
- Executa backup lógico (dump).
- Suporta compressão (Gzip).
- Gerencia retenção (Remove backups antigos).
"""
import sys
import os
import argparse
import logging
import subprocess
import shutil
from datetime import datetime
import glob
import time

# Setup path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

try:
    from automacao.utils.logging_config import setup_logging
except ImportError:
    # Fallback log
    logging.basicConfig(level=logging.INFO)

def run_backup(uri: str, out_dir: str, gzip_mode: bool = True):
    """Executa mongodump via subprocess."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(out_dir, f"backup_{timestamp}")
    
    cmd = ["mongodump", "--uri", uri, "--out", backup_path]
    if gzip_mode:
        cmd.append("--gzip")
        
    logging.info(f"🚀 Iniciando backup para: {backup_path}")
    
    try:
        # Mascara SENHA no log do comadndo
        safe_uri = uri.split("@")[-1] if "@" in uri else "localhost"
        logging.info(f"Command: mongodump ... {safe_uri}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logging.info("✅ Backup concluído com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Falha no backup: {e.stderr}")
        return False
    except FileNotFoundError:
        logging.error("❌ Executável 'mongodump' não encontrado no PATH.")
        return False

def clean_old_backups(out_dir: str, retention_days: int):
    """Remove backups mais antigos que X dias."""
    logging.info(f"🧹 Verificando retenção ({retention_days} dias)...")
    now = time.time()
    cutoff = now - (retention_days * 86400)
    
    # Lista diretórios em out_dir
    for item in os.listdir(out_dir):
        item_path = os.path.join(out_dir, item)
        if os.path.isdir(item_path) and item.startswith("backup_"):
            # Verifica data de modificação
            mtime = os.path.getmtime(item_path)
            if mtime < cutoff:
                logging.warning(f"🗑️ Removendo backup antigo: {item}")
                shutil.rmtree(item_path)

def main():
    parser = argparse.ArgumentParser(description="MongoDB Backup Manager")
    parser.add_argument("--uri", help="Mongo URI (Default: env MONGO_URI)")
    parser.add_argument("--out", default="./backups", help="Output directory")
    parser.add_argument("--days", type=int, default=7, help="Retention days")
    parser.add_argument("--json", action="store_true", help="JSON Logs")
    
    args = parser.parse_args()
    setup_logging(json_mode=args.json)
    
    uri = args.uri or os.environ.get("MONGO_URI")
    if not uri:
        logging.error("Defina MONGO_URI")
        sys.exit(1)
        
    # Cria dir se nao existe
    if not os.path.exists(args.out):
        os.makedirs(args.out)
        
    if run_backup(uri, args.out):
        clean_old_backups(args.out, args.days)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
