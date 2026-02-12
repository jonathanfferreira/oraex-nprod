"""
ORAEX - Connection Configuration
--------------------------------
Módulo centralizado para configuração de conexões Oracle.
Elimina duplicação de ConnectionConfig em múltiplos arquivos.

Uso:
    from automacao.utils.connection import ConnectionConfig
    
    # Via variáveis de ambiente
    config = ConnectionConfig.from_env()
    
    # Via argumentos explícitos
    config = ConnectionConfig(dsn="host:1521/orcl", username="sys", password="pwd")
    
    # Obter conexão
    conn = config.get_connection()
"""
import os
import logging
from typing import Optional

try:
    import cx_Oracle
except ImportError:
    cx_Oracle = None  # type: ignore


class ConnectionConfig:
    """Configuração centralizada de conexão Oracle."""
    
    def __init__(
        self, 
        dsn: str, 
        username: str, 
        password: str, 
        encoding: str = "UTF-8",
        mode: Optional[int] = None
    ):
        """
        Args:
            dsn: Data Source Name (host:port/service)
            username: Nome do usuário Oracle
            password: Senha do usuário
            encoding: Encoding da conexão (default: UTF-8)
            mode: Modo de conexão (ex: cx_Oracle.SYSDBA)
        """
        self.dsn = dsn
        self.username = username
        self.password = password
        self.encoding = encoding
        self.mode = mode
    
    @classmethod
    def from_env(
        cls,
        dsn_env: str = "ORACLE_DSN",
        user_env: str = "ORACLE_USER", 
        password_env: str = "ORACLE_PASSWORD",
        default_dsn: str = "localhost:1521/orcl",
        default_user: str = "system"
    ) -> "ConnectionConfig":
        """
        Cria configuração a partir de variáveis de ambiente.
        
        Environment Variables:
            ORACLE_DSN: Data Source Name (host:port/service)
            ORACLE_USER: Nome do usuário
            ORACLE_PASSWORD: Senha (obrigatória, sem default)
        
        Raises:
            ValueError: Se ORACLE_PASSWORD não estiver definida
        """
        dsn = os.environ.get(dsn_env, default_dsn)
        username = os.environ.get(user_env, default_user)
        password = os.environ.get(password_env)
        
        if not password:
            raise ValueError(
                "ORACLE_PASSWORD não definida. "
                "Configure a variável de ambiente ou use argumentos CLI: --password"
            )
        
        return cls(dsn=dsn, username=username, password=password)
    
    @classmethod
    def from_cli(
        cls,
        cli_dsn: Optional[str] = None,
        cli_user: Optional[str] = None,
        cli_password: Optional[str] = None
    ) -> "ConnectionConfig":
        """
        Cria configuração mesclando CLI args com variáveis de ambiente.
        Prioridade: CLI > Environment > Default
        """
        dsn = cli_dsn or os.environ.get("ORACLE_DSN", "localhost:1521/orcl")
        username = cli_user or os.environ.get("ORACLE_USER", "system")
        password = cli_password or os.environ.get("ORACLE_PASSWORD")

        if not password:
            raise ValueError(
                "Senha não fornecida. Use --password ou configure ORACLE_PASSWORD."
            )
        
        return cls(dsn=dsn, username=username, password=password)
    
    def get_connection(self) -> "cx_Oracle.Connection":
        """
        Estabelece e retorna uma conexão Oracle.
        
        Returns:
            cx_Oracle.Connection: Conexão ativa
            
        Raises:
            cx_Oracle.Error: Se a conexão falhar
            ImportError: Se cx_Oracle não estiver instalado
        """
        if cx_Oracle is None:
            raise ImportError(
                "cx_Oracle não está instalado. "
                "Execute: pip install cx_Oracle"
            )
        
        connect_args = {
            "user": self.username,
            "password": self.password,
            "dsn": self.dsn,
            "encoding": self.encoding
        }
        
        if self.mode is not None:
            connect_args["mode"] = self.mode
        
        logging.debug(f"Conectando a {self.dsn} como {self.username}")
        return cx_Oracle.connect(**connect_args)
    
    def __repr__(self) -> str:
        return f"ConnectionConfig(dsn='{self.dsn}', username='{self.username}')"


# Alias para compatibilidade com código existente
def get_connection_config(
    cli_dsn: Optional[str] = None,
    cli_user: Optional[str] = None,
    cli_password: Optional[str] = None
) -> ConnectionConfig:
    """
    Função de conveniência para criar ConnectionConfig.
    Mantida para compatibilidade com padrão existente.
    """
    return ConnectionConfig.from_cli(cli_dsn, cli_user, cli_password)
