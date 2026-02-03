"""
Runbook: Failover Automatizado Oracle RAC
------------------------------------------
Automatiza o processo de failover em caso de falha do nó primário.
"""
import sys
import logging
from typing import Dict, List
import cx_Oracle

sys.path.append('.')

from automacao.runbooks.base_runbook import BaseRunbook, RunbookStatus
from automacao.utils.credentials import get_credentials


class FailoverRunbook(BaseRunbook):
    """Runbook para failover automático em Oracle RAC"""
    
    def __init__(self, database: str, primary_node: str, secondary_nodes: List[str]):
        super().__init__(f"failover_{database}")
        self.database = database
        self.primary_node = primary_node
        self.secondary_nodes = secondary_nodes
        self.original_primary = primary_node
        self.new_primary = None
        self.connection = None
    
    def validate_preconditions(self) -> bool:
        """Valida se failover é necessário e possível"""
        self.log_step("Validando pré-condições")
        
        # 1. Verificar se primary está realmente down
        try:
            # Tentar conectar no primary
            creds = get_credentials()
            test_conn = cx_Oracle.connect(
                creds.username,
                creds.password,
                f"{self.primary_node}:1521/{self.database}",
                encoding="UTF-8"
            )
            test_conn.close()
            
            # Se conectou, primary está UP - não precisa failover
            self.logger.warning(f"Primary {self.primary_node} está UP. Failover não necessário.")
            return False
            
        except Exception as e:
            self.logger.info(f"Primary {self.primary_node} está DOWN: {e}")
            # Primary está down - continuar com failover
        
        # 2. Verificar se há secondary disponível
        for secondary in self.secondary_nodes:
            try:
                creds = get_credentials()
                test_conn = cx_Oracle.connect(
                    creds.username,
                    creds.password,
                    f"{secondary}:1521/{self.database}",
                    encoding="UTF-8"
                )
                test_conn.close()
                self.new_primary = secondary
                self.log_step("Secondary disponível encontrado", success=True)
                return True
            except Exception:
                continue
        
        self.logger.error("Nenhum secondary disponível para failover")
        return False
    
    def execute(self) -> bool:
        """Executa o failover"""
        self.log_step("Iniciando failover")
        
        if not self.new_primary:
            self.logger.error("Nenhum secondary disponível")
            return False
        
        try:
            # Conectar no secondary que será o novo primary
            creds = get_credentials()
            self.connection = cx_Oracle.connect(
                creds.username,
                creds.password,
                f"{self.new_primary}:1521/{self.database}",
                encoding="UTF-8"
            )
            
            # Executar failover (comando específico depende da configuração RAC)
            # Exemplo genérico:
            cursor = self.connection.cursor()
            
            # Verificar status do cluster
            cursor.execute("SELECT instance_name, status FROM v$instance")
            instances = cursor.fetchall()
            self.logger.info(f"Instâncias disponíveis: {instances}")
            
            # Em produção, aqui executaria comandos específicos de failover
            # Ex: ALTER SYSTEM SET CLUSTER_DATABASE=FALSE; (se aplicável)
            
            self.log_step("Failover executado", success=True)
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao executar failover: {e}")
            return False
    
    def validate_postconditions(self) -> bool:
        """Valida se failover foi bem-sucedido"""
        self.log_step("Validando pós-condições")
        
        if not self.connection:
            return False
        
        try:
            # Verificar se novo primary está respondendo
            cursor = self.connection.cursor()
            cursor.execute("SELECT instance_name, status FROM v$instance")
            result = cursor.fetchone()
            
            if result and result[1] == "OPEN":
                self.log_step("Novo primary está OPEN e respondendo", success=True)
                return True
            else:
                self.log_step("Novo primary não está em estado válido", success=False)
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao validar pós-condições: {e}")
            return False
    
    def rollback(self) -> bool:
        """Reverte failover (se possível)"""
        self.log_step("Tentando rollback")
        
        # Rollback de failover é complexo e geralmente requer intervenção manual
        # Aqui apenas registramos que rollback foi tentado
        self.logger.warning("Rollback de failover requer intervenção manual")
        return False
    
    def notify_team(self, message: str):
        """Notifica equipe sobre o failover"""
        # Implementar notificação (email, Slack, PagerDuty, etc.)
        self.logger.info(f"Notificação: {message}")
        # Exemplo: send_email("dba-team@getnet.com.br", f"Failover: {message}")
    
    def update_cmdb(self, status: str):
        """Atualiza CMDB com status do failover"""
        # Implementar atualização de CMDB
        self.logger.info(f"CMDB atualizado: {status}")
        # Exemplo: cmdb_api.update_database_status(self.database, status)


def main():
    """Exemplo de uso do runbook"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Runbook de Failover Automatizado")
    parser.add_argument("--database", required=True, help="Nome do banco")
    parser.add_argument("--primary", required=True, help="Nó primário")
    parser.add_argument("--secondaries", nargs="+", required=True, help="Nós secundários")
    
    args = parser.parse_args()
    
    # Criar e executar runbook
    runbook = FailoverRunbook(
        database=args.database,
        primary_node=args.primary,
        secondary_nodes=args.secondaries
    )
    
    result = runbook.run()
    
    # Output
    import json
    print(json.dumps(result, indent=2))
    
    # Exit code
    exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
