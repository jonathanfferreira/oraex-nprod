import os
import logging
from typing import NamedTuple, Optional

class DBCredentials(NamedTuple):
    username: str
    password: str
    dsn: str

def get_credentials(
    cli_user: Optional[str] = None, 
    cli_password: Optional[str] = None, 
    cli_dsn: Optional[str] = None
) -> DBCredentials:
    """
    Resolve credenciais seguindo a ordem de prioridade:
    1. Argumentos de Linha de Comando (CLI) - Se fornecidos explicitamente
    2. Variáveis de Ambiente (ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN)
    3. Defaults (apenas para fallback, com aviso de log)
    """
    
    # 1. Username
    username = cli_user or os.environ.get("ORACLE_USER") or "system"
    
    # 2. DSN
    dsn = cli_dsn or os.environ.get("ORACLE_DSN") or "localhost:1521/orcl"
    
    # 3. Password (Tratamento especial de segurança)
    env_password = os.environ.get("ORACLE_PASSWORD")
    
    if cli_password and cli_password != "oracle": 
        # Assumindo "oracle" como o default antigo do argparse que queremos ignorar se tiver ENV
        password = cli_password
    elif env_password:
        password = env_password
    else:
        password = cli_password if cli_password else None
        if not password:
            raise ValueError(
                "Senha não fornecida. Use --password ou configure ORACLE_PASSWORD."
            )

    return DBCredentials(username, password, dsn)
