"""
ORAEX - Maintenance Mode Manager
--------------------------------
Gerencia janelas de manutenção (GMUD) para evitar que automações
atuem durante janelas planejadas.

Mecanismo:
Verifica a existência do arquivo de bloqueio (MAINTENANCE.LOCK).
Se existir, interrompe a execução dos scripts de automação.

Uso:
    from automacao.utils.maintenance import MaintenanceManager
    
    if MaintenanceManager.is_active():
        sys.exit(0) # Sai silenciosamente ou com log informativo
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Caminho do arquivo de lock (Padrão Linux)
# Em produção pode ser /tmp/oraex_maintenance.lock ou /var/lock/oraex.lock
# Aqui usamos relativo para portabilidade
LOCK_FILE_NAME = "ORAEX_MAINTENANCE.lock"

class MaintenanceManager:
    
    @staticmethod
    def _get_lock_path() -> Path:
        """Resolve o caminho do arquivo de lock."""
        # Tenta usar path relativo à raiz do projeto se possível, ou /tmp
        base_dir = Path(__file__).resolve().parent.parent.parent
        return base_dir / LOCK_FILE_NAME

    @staticmethod
    def is_active() -> bool:
        """Verifica se o modo de manutenção está ativo."""
        lock_file = MaintenanceManager._get_lock_path()
        
        if lock_file.exists():
            logging.warning(f"🛑 MODO MANUTENÇÃO ATIVO! (Arquivo detectado: {lock_file})")
            logging.warning("   -> ORAEX: Execução suspensa para respeitar janela de GMUD.")
            return True
            
        return False

    @staticmethod
    def enable(reason: str = "GMUD Generica"):
        """Ativa modo manutenção."""
        lock_file = MaintenanceManager._get_lock_path()
        with open(lock_file, "w") as f:
            f.write(f"Maintenance Enabled at {datetime.now().isoformat()}\n")
            f.write(f"Reason: {reason}\n")
        print(f"✅ Modo Manutenção ATIVADO. Automações paradas.")
        print(f"   Lock file: {lock_file}")

    @staticmethod
    def disable():
        """Desativa modo manutenção."""
        lock_file = MaintenanceManager._get_lock_path()
        if lock_file.exists():
            os.remove(lock_file)
            print("✅ Modo Manutenção DESATIVADO. Automações liberadas.")
        else:
            print("ℹ️  Modo Manutenção já estava inativo.")

if __name__ == "__main__":
    # CLI simples para teste
    if len(sys.argv) > 1:
        if sys.argv[1] == "on":
            MaintenanceManager.enable(sys.argv[2] if len(sys.argv) > 2 else "Manual CLI")
        elif sys.argv[1] == "off":
            MaintenanceManager.disable()
        elif sys.argv[1] == "status":
            active = MaintenanceManager.is_active()
            print(f"Status: {'ATIVO 🛑' if active else 'INATIVO 🟢'}")
    else:
        print("Uso: python maintenance.py [on|off|status]")
