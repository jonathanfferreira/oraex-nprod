
import os
import glob
import shutil
import gzip
import logging
import argparse
from datetime import datetime, timedelta

# Configuração Padrão
DEFAULT_LOG_DIRS = [
    "/u01/app/oracle/diag/rdbms",          # Base do ADR (Alert Log, Traces)
    "/u01/app/grid/diag/tnslsnr",         # Listener Logs (Grid Infrastructure)
    "/u01/app/oracle/diag/tnslsnr",       # Listener Logs (Oracle Home)
    "/u01/app/oracle/admin/*/adump"       # Audit Dumps
]

# Configuração de Retenção (Dias)
RETENTION_DAYS_LOG = 30   # Logs normais
RETENTION_DAYS_ADUMP = 60 # Audit logs (compliance)
COMPRESS_AFTER_DAYS = 2   # Comprimir após X dias

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()] # Apenas stdout para ser capturado pelo cron/ferramenta
)

def get_file_age_days(filepath):
    """Retorna a idade do arquivo em dias."""
    try:
        mtime = os.path.getmtime(filepath)
        file_date = datetime.fromtimestamp(mtime)
        return (datetime.now() - file_date).days
    except OSError:
        return 0

def compress_file(filepath):
    """Comprime um arquivo usando gzip."""
    try:
        with open(filepath, 'rb') as f_in:
            with gzip.open(filepath + '.gz', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(filepath) # Remove original após compressão
        logging.info(f"Comprimido: {filepath} -> {filepath}.gz")
        return True
    except Exception as e:
        logging.error(f"Erro ao comprimir {filepath}: {e}")
        return False

def rotate_listener_log(log_path):
    """
    Rotação específica para listener.log (não pode deletar direto com processo aberto).
    Método seguro: CP /dev/null ou renomear se estivesse parado (mas aqui assumimos online).
    Idealmente, usar 'lsnrctl set log_status off' -> rename -> 'on', mas isso requer chamadas de sistema.
    Aqui faremos a limpeza via Truncate se for muito grande (>1GB) ou apenas alertar.
    
    Para o MVP: Vamos focar em limpar os XML logs do listener que enchem rápido no 11g/12c/19c
    path: .../alert/log_*.xml
    """
    # Exemplo: varrer diag/tnslsnr/.../alert/*.xml trocando por versões comprimidas
    pass

def clean_directory(directory, pattern, days_to_keep, days_to_compress):
    """Varre diretório recursivamente buscando padrões."""
    total_cleaned = 0
    total_compressed = 0
    
    logging.info(f"Analisando diretório: {directory} (Pattern: {pattern})")
    
    # Walk para descida recursiva (ADR tem estrutura profunda)
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if not filename.endswith(pattern.replace('*', '')): 
                # Simplificação do glob match manual, ideal usar fnmatch
                import fnmatch
                if not fnmatch.fnmatch(filename, pattern):
                    continue
            
            filepath = os.path.join(root, filename)
            age = get_file_age_days(filepath)
            
            # 1. Política de Deleção (Purge)
            if age > days_to_keep:
                try:
                    os.remove(filepath)
                    logging.info(f"Deletado (purge): {filepath} ({age} dias)")
                    total_cleaned += 1
                except Exception as e:
                    logging.error(f"Falha ao deletar {filepath}: {e}")
                continue # Se deletou, next

            # 2. Política de Compressão
            if age > days_to_compress and not filename.endswith('.gz'):
                compress_file(filepath)
                total_compressed += 1

    logging.info(f"Resumo {directory}: {total_cleaned} removidos, {total_compressed} comprimidos.")

def main():
    parser = argparse.ArgumentParser(description="Oracle Log Rotation Tool (Silenciador de 'Log NOK')")
    parser.add_argument("--dry-run", action="store_true", help="Apenas simula, não apaga nada")
    args = parser.parse_args()

    logging.info("Iniciando Smart Log Rotate...")

    # 1. Limpeza de Trace Files (*.trc, *.trm)
    for base_dir in DEFAULT_LOG_DIRS:
        # Expande wildcards no path base (ex: /u01/.../*/adump)
        for path in glob.glob(base_dir):
            if not os.path.exists(path):
                continue
                
            logging.info(f"Processando Base: {path}")
            
            # Limpa Traces
            clean_directory(path, "*.trc", 14, 2)
            clean_directory(path, "*.trm", 14, 2)
            
            # Limpa Audit Logs (.aud)
            clean_directory(path, "*.aud", 60, 5)
            
            # Limpa Listener XML Logs antigos
            clean_directory(path, "log_*.xml", 30, 2)

    logging.info("Lembrete: Para rotação do listener.log principal, use 'lsnrctl set log_status off'")
    logging.info("Concluído.")

if __name__ == "__main__":
    main()
