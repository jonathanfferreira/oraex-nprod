import logging
import sys
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """
    Formatador de log customizado para saída JSON estruturada.
    Ideal para ferramentas como Splunk, ELK, Datadog.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "path": record.pathname,
            "line": record.lineno,
        }
        
        # Inclui exception info se houver
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        # Inclui extra fields se passados no logging.info(..., extra={...})
        if hasattr(record, 'extra_data'):
            log_record.update(record.extra_data)

        return json.dumps(log_record)

def setup_logging(
    log_file: str = None, 
    json_mode: bool = False, 
    level: int = logging.INFO
) -> None:
    """
    Configura o logging global da aplicação.
    
    Args:
        log_file: Caminho opcional para arquivo de log.
        json_mode: Se True, emite logs em formato JSON (stdout e arquivo).
        level: Nível de log (default INFO).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Limpa handlers existentes para evitar duplicação em re-execuções ou imports
    if root_logger.handlers:
        root_logger.handlers = []

    # Configura Formatter
    if json_mode:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    # Handler de Console (Stderr para não poluir stdout que pode ser PIPE)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Handler de Arquivo (Opcional)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    logging.info(f"Logging configurado via utils. (JSON Mode: {json_mode})")
