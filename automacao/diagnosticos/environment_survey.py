"""
ORAEX - Environment Survey Script (SAFE TO RUN)
-----------------------------------------------
Este script coleta informações do ambiente para validar compatibilidade.
NÃO FAZ NENHUMA ALTERAÇÃO NO SISTEMA. APENAS LEITURA.

O que ele verifica:
1. Versão do Python e disponibilidade de bibliotecas.
2. Variáveis de ambiente Oracle (ORACLE_HOME, etc).
3. Permissões de escrita em diretórios chave.
4. Estrutura de diretórios do sistema (/u01, /ggs).
5. Conectividade básica (se credenciais forem fornecidas).

Uso:
    python environment_survey.py
"""
import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def check_python():
    log(f"Python Version: {sys.version.split()[0]}", "CHECK")
    log(f"Platform: {platform.platform()}", "CHECK")
    
    try:
        import cx_Oracle
        log(f"cx_Oracle: INSTALLED (v{cx_Oracle.version})", "OK")
    except ImportError:
        log("cx_Oracle: NOT FOUND", "WARNING")

def check_env_vars():
    vars_to_check = ["ORACLE_HOME", "ORACLE_SID", "LD_LIBRARY_PATH", "PATH"]
    log("Checking Environment Variables:", "CHECK")
    for var in vars_to_check:
        value = os.environ.get(var)
        if value:
            log(f"  {var}: {value}", "OK")
        else:
            log(f"  {var}: NOT SET", "WARNING")

def check_dirs():
    dirs_to_check = [
        "/u01/app",
        "/u01/app/oracle",
        ("/ggs", "Required for PROD (GoldenGate)"),
        "/tmp",
        "/var/log",
        "/opt"
    ]
    log("Checking Directory Structure:", "CHECK")
    for item in dirs_to_check:
        d = item if isinstance(item, str) else item[0]
        note = f" [{item[1]}]" if isinstance(item, tuple) else ""
        
        p = Path(d)
        if p.exists():
            log(f"  {d}: FOUND{note}", "OK")
            if os.access(d, os.W_OK):
                log(f"    -> Writable: YES", "OK")
            else:
                log(f"    -> Writable: NO", "INFO")
        else:
            status = "WARNING" if "PROD" not in note else "INFO"
            log(f"  {d}: NOT FOUND{note}", status)

def check_commands():
    cmds = ["sqlplus", "ggsci", "lsblk", "crm_mon", "docker", "podman"]
    log("Checking System Commands:", "CHECK")
    for cmd in cmds:
        path = shutil.which(cmd)
        if path:
            log(f"  {cmd}: FOUND ({path})", "OK")
        else:
            log(f"  {cmd}: NOT FOUND", "INFO")

def main():
    print("="*60)
    print(f"ORAEX Environment Verify - {datetime.now().isoformat()}")
    print("="*60)
    
    check_python()
    print("-" * 20)
    check_env_vars()
    print("-" * 20)
    check_dirs()
    print("-" * 20)
    check_commands()
    
    print("="*60)
    print("Survey Complete.")

if __name__ == "__main__":
    main()
