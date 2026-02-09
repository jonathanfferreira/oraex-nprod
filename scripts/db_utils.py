"""
ORAEX - Database Utilities (Modernized)
---------------------------------------
Handles database connections using 'oracledb' (Thin Mode by default).
Supports fallback to 'cx_Oracle' if necessary, but prioritizes modern driver.

Usage:
    from db_utils import get_connection

    conn = get_connection()
    cursor = conn.cursor()
"""
import os
import logging
import sys

# Tenta importar oracledb (Padrão 2025+), fallback para cx_Oracle
try:
    import oracledb as db_driver
    DRIVER_NAME = 'oracledb'
except ImportError:
    try:
        import cx_Oracle as db_driver
        DRIVER_NAME = 'cx_Oracle'
    except ImportError:
        print("❌ Error: No Oracle Driver found. Install 'oracledb' or 'cx_Oracle'.")
        sys.exit(1)

# Configuração de Logging simples
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_env_credentials():
    """
    Recupera credenciais das variáveis de ambiente padrão.
    Estas variáveis devem ser setadas pelo .db_profile_oraex ou Ansible.
    
    Returns:
        tuple: (user, password, dsn)
    """
    user = os.getenv('ORACLE_USER', 'system')
    password = os.getenv('ORACLE_PASSWORD')
    dsn = os.getenv('ORACLE_DSN', 'localhost:1521/oraex')
    
    if not password:
        # Fallback para Lab (Hardcoded) - EM PROD ISSO DARIA ERRO
        logging.warning("⚠️  ORACLE_PASSWORD not set. Using lab default.")
        password = 'oracle' 
        
    return user, password, dsn

def get_connection():
    """
    Estabelece conexão com o banco de dados.
    Tenta Thin Mode primeiro (sem Instant Client).
    """
    user, password, dsn = get_env_credentials()
    
    logging.debug(f"Connecting to {dsn} as {user} using {DRIVER_NAME}...")
    
    try:
        if DRIVER_NAME == 'oracledb':
            # Thin mode by default (no params needed usually)
            conn = db_driver.connect(user=user, password=password, dsn=dsn)
        else:
            conn = db_driver.connect(user, password, dsn)
            
        return conn
    except db_driver.Error as e:
        logging.error(f"❌ Connection Failed: {e}")
        raise

def execute_query(conn, sql, params=None):
    """Helper para executar Select e retornar lista de dicts."""
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
            
        columns = [col[0].lower() for col in cursor.description]
        rows = cursor.fetchall()
        
        return [dict(zip(columns, row)) for row in rows]
    finally:
        cursor.close()
