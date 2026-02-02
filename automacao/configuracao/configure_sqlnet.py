#!/usr/bin/env python3
"""
CONFIGURE_SQLNET.PY - Tuning de Rede Oracle (Item 10 do Book DBA)
=================================================================

Objetivo: Garantir que os arquivos sqlnet.ora e listener.ora tenham os 
parâmetros obrigatórios para evitar problemas de conexão "Dead Connection".

Parâmetros obrigatórios (Book DBA Getnet):
- SQLNET.EXPIRE_TIME = 2          (Detecta conexões mortas a cada 2 minutos)
- SQLNET.INBOUND_CONNECT_TIMEOUT = 120  (Timeout de handshake)
- SQLNET.AUTHENTICATION_SERVICES = (NONE)  (Desabilita autenticação OS)

Uso:
  python configure_sqlnet.py --oracle-home /u01/app/oracle/product/19c/dbhome_1
  python configure_sqlnet.py --oracle-home /u01/app/oracle/product/19c/dbhome_1 --apply

Autor: ORAEX Automation Team
"""

import os
import sys
import argparse
import logging
import shutil
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Parâmetros obrigatórios conforme Book DBA
REQUIRED_SQLNET_PARAMS = {
    "SQLNET.EXPIRE_TIME": "2",
    "SQLNET.INBOUND_CONNECT_TIMEOUT": "120",
    "SQLNET.AUTHENTICATION_SERVICES": "(NONE)",
    "SQLNET.RECV_TIMEOUT": "120",
    "SQLNET.SEND_TIMEOUT": "120"
}

# Parâmetros recomendados para o Listener
REQUIRED_LISTENER_PARAMS = {
    "INBOUND_CONNECT_TIMEOUT_LISTENER": "120",
    "SUBSCRIBE_FOR_NODE_DOWN_EVENT_LISTENER": "OFF"  # Em RAC, pode causar overhead
}


class SQLNetConfigurator:
    """
    Classe para ler, validar e corrigir arquivos de configuração SQLNet.
    """
    
    def __init__(self, oracle_home: str):
        self.oracle_home = oracle_home
        self.network_admin = os.path.join(oracle_home, "network", "admin")
        self.sqlnet_file = os.path.join(self.network_admin, "sqlnet.ora")
        self.listener_file = os.path.join(self.network_admin, "listener.ora")
        self.backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def validate_paths(self) -> bool:
        """Verifica se os caminhos existem."""
        if not os.path.isdir(self.oracle_home):
            logging.error(f"ORACLE_HOME não encontrado: {self.oracle_home}")
            return False
            
        if not os.path.isdir(self.network_admin):
            logging.error(f"Diretório network/admin não encontrado: {self.network_admin}")
            return False
            
        return True
    
    def backup_file(self, filepath: str) -> Optional[str]:
        """Cria backup do arquivo antes de modificar."""
        if not os.path.exists(filepath):
            return None
            
        backup_path = f"{filepath}.bak.{self.backup_suffix}"
        try:
            shutil.copy2(filepath, backup_path)
            logging.info(f"Backup criado: {backup_path}")
            return backup_path
        except Exception as e:
            logging.error(f"Erro ao criar backup de {filepath}: {e}")
            return None
    
    def parse_ora_file(self, filepath: str) -> Dict[str, str]:
        """
        Lê um arquivo .ora e extrai os parâmetros em formato KEY=VALUE.
        
        Nota: Arquivos .ora podem ter sintaxe complexa (listas, blocos).
        Esta função foca nos parâmetros simples no formato KEY = VALUE.
        """
        params = {}
        
        if not os.path.exists(filepath):
            logging.warning(f"Arquivo não existe: {filepath}")
            return params
            
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                
            # Remove comentários (linhas que começam com #)
            lines = [l.strip() for l in content.splitlines() if l.strip() and not l.strip().startswith('#')]
            
            # Junta linhas continuadas (linhas que terminam com \)
            joined_lines = []
            current_line = ""
            for line in lines:
                if line.endswith('\\'):
                    current_line += line[:-1]
                else:
                    current_line += line
                    joined_lines.append(current_line)
                    current_line = ""
            
            # Extrai parâmetros KEY = VALUE
            for line in joined_lines:
                # Ignora blocos complexos (ex: LISTENER = ...)
                if '=' in line:
                    # Tenta separar no primeiro '='
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        key = parts[0].strip().upper()
                        value = parts[1].strip()
                        params[key] = value
                        
        except Exception as e:
            logging.error(f"Erro ao ler {filepath}: {e}")
            
        return params
    
    def check_sqlnet_compliance(self) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """
        Verifica se sqlnet.ora tem os parâmetros obrigatórios.
        
        Retorna:
        - missing: Parâmetros que não existem
        - wrong: Parâmetros com valor incorreto {param: (atual, esperado)}
        - ok: Parâmetros corretos
        """
        current_params = self.parse_ora_file(self.sqlnet_file)
        
        missing = {}
        wrong = {}
        ok = {}
        
        for param, expected_value in REQUIRED_SQLNET_PARAMS.items():
            if param not in current_params:
                missing[param] = expected_value
            elif current_params[param] != expected_value:
                wrong[param] = (current_params[param], expected_value)
            else:
                ok[param] = expected_value
                
        return missing, wrong, ok
    
    def check_listener_compliance(self) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """
        Verifica se listener.ora tem os parâmetros obrigatórios.
        """
        current_params = self.parse_ora_file(self.listener_file)
        
        missing = {}
        wrong = {}
        ok = {}
        
        for param, expected_value in REQUIRED_LISTENER_PARAMS.items():
            if param not in current_params:
                missing[param] = expected_value
            elif current_params[param] != expected_value:
                wrong[param] = (current_params[param], expected_value)
            else:
                ok[param] = expected_value
                
        return missing, wrong, ok
    
    def add_missing_params(self, filepath: str, params: Dict[str, str], dry_run: bool = True) -> bool:
        """
        Adiciona parâmetros faltantes ao arquivo .ora.
        """
        if not params:
            return True
            
        if dry_run:
            logging.info(f"[DRY-RUN] Adicionaria ao {os.path.basename(filepath)}:")
            for param, value in params.items():
                logging.info(f"  {param} = {value}")
            return True
            
        try:
            # Cria backup antes de modificar
            self.backup_file(filepath)
            
            # Lê conteúdo atual (ou cria vazio)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
            else:
                content = ""
                
            # Adiciona cabeçalho se arquivo vazio
            if not content.strip():
                content = f"# {os.path.basename(filepath)} - Configurado por ORAEX Automation\n"
                content += f"# Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # Adiciona linha separadora e novos parâmetros
            content += f"\n# === Parâmetros adicionados por configure_sqlnet.py ({datetime.now().strftime('%Y-%m-%d')}) ===\n"
            for param, value in params.items():
                content += f"{param} = {value}\n"
                
            # Escreve de volta
            with open(filepath, 'w') as f:
                f.write(content)
                
            logging.info(f"Parâmetros adicionados em {filepath}")
            return True
            
        except Exception as e:
            logging.error(f"Erro ao modificar {filepath}: {e}")
            return False
    
    def fix_wrong_params(self, filepath: str, wrong_params: Dict[str, Tuple[str, str]], dry_run: bool = True) -> bool:
        """
        Corrige parâmetros com valor incorreto.
        wrong_params: {param: (valor_atual, valor_correto)}
        """
        if not wrong_params:
            return True
            
        if dry_run:
            logging.info(f"[DRY-RUN] Corrigiria em {os.path.basename(filepath)}:")
            for param, (atual, correto) in wrong_params.items():
                logging.info(f"  {param}: '{atual}' -> '{correto}'")
            return True
            
        try:
            # Backup
            self.backup_file(filepath)
            
            with open(filepath, 'r') as f:
                content = f.read()
                
            # Substitui cada parâmetro incorreto
            for param, (atual, correto) in wrong_params.items():
                # Padrão: PARAM = VALOR (com espaços variáveis)
                pattern = rf"^(\s*{re.escape(param)}\s*=\s*).*$"
                replacement = rf"\g<1>{correto}"
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.IGNORECASE)
                
            with open(filepath, 'w') as f:
                f.write(content)
                
            logging.info(f"Parâmetros corrigidos em {filepath}")
            return True
            
        except Exception as e:
            logging.error(f"Erro ao corrigir {filepath}: {e}")
            return False
    
    def generate_report(self) -> Dict:
        """
        Gera relatório completo de compliance.
        """
        report = {
            "oracle_home": self.oracle_home,
            "sqlnet": {
                "file": self.sqlnet_file,
                "exists": os.path.exists(self.sqlnet_file),
                "missing": {},
                "wrong": {},
                "ok": {}
            },
            "listener": {
                "file": self.listener_file,
                "exists": os.path.exists(self.listener_file),
                "missing": {},
                "wrong": {},
                "ok": {}
            }
        }
        
        # Verifica sqlnet.ora
        missing, wrong, ok = self.check_sqlnet_compliance()
        report["sqlnet"]["missing"] = missing
        report["sqlnet"]["wrong"] = wrong
        report["sqlnet"]["ok"] = ok
        
        # Verifica listener.ora
        missing, wrong, ok = self.check_listener_compliance()
        report["listener"]["missing"] = missing
        report["listener"]["wrong"] = wrong
        report["listener"]["ok"] = ok
        
        return report
    
    def apply_fixes(self, dry_run: bool = True) -> bool:
        """
        Aplica todas as correções necessárias.
        """
        success = True
        
        # SQLNet
        missing, wrong, ok = self.check_sqlnet_compliance()
        if missing:
            if not self.add_missing_params(self.sqlnet_file, missing, dry_run):
                success = False
        if wrong:
            if not self.fix_wrong_params(self.sqlnet_file, wrong, dry_run):
                success = False
                
        # Listener
        missing, wrong, ok = self.check_listener_compliance()
        if missing:
            if not self.add_missing_params(self.listener_file, missing, dry_run):
                success = False
        if wrong:
            if not self.fix_wrong_params(self.listener_file, wrong, dry_run):
                success = False
                
        return success


def print_report(report: Dict):
    """Imprime relatório formatado."""
    print("\n" + "="*70)
    print("RELATÓRIO DE COMPLIANCE - SQLNET/LISTENER")
    print("="*70)
    print(f"ORACLE_HOME: {report['oracle_home']}")
    print()
    
    for file_type in ['sqlnet', 'listener']:
        info = report[file_type]
        print(f"--- {file_type.upper()}.ORA ---")
        print(f"Arquivo: {info['file']}")
        print(f"Existe: {'SIM' if info['exists'] else 'NÃO'}")
        
        if info['ok']:
            print(f"  ✅ OK ({len(info['ok'])} parâmetros corretos)")
            
        if info['missing']:
            print(f"  ❌ FALTANDO ({len(info['missing'])} parâmetros):")
            for param, value in info['missing'].items():
                print(f"      {param} = {value}")
                
        if info['wrong']:
            print(f"  ⚠️  INCORRETOS ({len(info['wrong'])} parâmetros):")
            for param, (atual, correto) in info['wrong'].items():
                print(f"      {param}: '{atual}' deveria ser '{correto}'")
                
        print()
    
    # Status geral
    total_issues = sum(
        len(report[ft]['missing']) + len(report[ft]['wrong']) 
        for ft in ['sqlnet', 'listener']
    )
    
    if total_issues == 0:
        print("✅ COMPLIANCE: TODOS OS PARÂMETROS ESTÃO CORRETOS!")
    else:
        print(f"⚠️  COMPLIANCE: {total_issues} PROBLEMA(S) ENCONTRADO(S)")
        print("   Execute com --apply para corrigir automaticamente.")
    
    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Configurador SQLNet - Garante compliance com Book DBA Getnet"
    )
    parser.add_argument(
        "--oracle-home", 
        required=True,
        help="Caminho do ORACLE_HOME (ex: /u01/app/oracle/product/19c/dbhome_1)"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica as correções (padrão é apenas verificar)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Saída em formato JSON (para integração)"
    )
    
    args = parser.parse_args()
    
    configurator = SQLNetConfigurator(args.oracle_home)
    
    if not configurator.validate_paths():
        sys.exit(1)
    
    # Gera relatório
    report = configurator.generate_report()
    
    if args.json:
        import json
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
    
    # Aplica correções se solicitado
    if args.apply:
        logging.info("Aplicando correções...")
        if configurator.apply_fixes(dry_run=False):
            logging.info("✅ Correções aplicadas com sucesso!")
            logging.info("IMPORTANTE: Reinicie o Listener para aplicar as mudanças:")
            logging.info("  lsnrctl reload LISTENER")
        else:
            logging.error("❌ Algumas correções falharam.")
            sys.exit(1)
    else:
        # Mostra o que seria feito
        configurator.apply_fixes(dry_run=True)


if __name__ == "__main__":
    main()
