"""
Base Runbook - Classe abstrata para todos os runbooks
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from enum import Enum
import logging


class RunbookStatus(Enum):
    """Status de execução de um runbook"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class BaseRunbook(ABC):
    """Classe base para todos os runbooks automatizados"""
    
    def __init__(self, name: str):
        self.name = name
        self.status = RunbookStatus.PENDING
        self.steps_executed = []
        self.errors = []
        self.logger = logging.getLogger(f"runbook.{name}")
    
    @abstractmethod
    def validate_preconditions(self) -> bool:
        """Valida pré-condições antes de executar"""
        pass
    
    @abstractmethod
    def execute(self) -> bool:
        """Executa o runbook"""
        pass
    
    @abstractmethod
    def validate_postconditions(self) -> bool:
        """Valida pós-condições após execução"""
        pass
    
    @abstractmethod
    def rollback(self) -> bool:
        """Reverte mudanças em caso de falha"""
        pass
    
    def run(self) -> Dict:
        """Executa o runbook completo com tratamento de erros"""
        self.status = RunbookStatus.RUNNING
        self.logger.info(f"Iniciando runbook: {self.name}")
        
        try:
            # 1. Validar pré-condições
            if not self.validate_preconditions():
                self.status = RunbookStatus.FAILED
                self.errors.append("Pré-condições não atendidas")
                return self._get_result()
            
            # 2. Executar
            if not self.execute():
                self.status = RunbookStatus.FAILED
                self.errors.append("Falha na execução")
                # Tentar rollback
                if self.rollback():
                    self.status = RunbookStatus.ROLLED_BACK
                return self._get_result()
            
            # 3. Validar pós-condições
            if not self.validate_postconditions():
                self.status = RunbookStatus.FAILED
                self.errors.append("Pós-condições não atendidas")
                # Tentar rollback
                if self.rollback():
                    self.status = RunbookStatus.ROLLED_BACK
                return self._get_result()
            
            # Sucesso
            self.status = RunbookStatus.SUCCESS
            self.logger.info(f"Runbook concluído com sucesso: {self.name}")
            return self._get_result()
            
        except Exception as e:
            self.status = RunbookStatus.FAILED
            self.errors.append(str(e))
            self.logger.error(f"Erro ao executar runbook: {e}")
            
            # Tentar rollback
            try:
                if self.rollback():
                    self.status = RunbookStatus.ROLLED_BACK
            except Exception as rollback_error:
                self.errors.append(f"Erro no rollback: {rollback_error}")
            
            return self._get_result()
    
    def _get_result(self) -> Dict:
        """Retorna resultado do runbook"""
        return {
            "name": self.name,
            "status": self.status.value,
            "steps_executed": self.steps_executed,
            "errors": self.errors,
            "success": self.status == RunbookStatus.SUCCESS
        }
    
    def log_step(self, step_name: str, success: bool = True):
        """Registra um passo executado"""
        self.steps_executed.append({
            "step": step_name,
            "success": success,
            "timestamp": None  # Adicionar timestamp se necessário
        })
        if success:
            self.logger.info(f"Step concluído: {step_name}")
        else:
            self.logger.warning(f"Step falhou: {step_name}")
