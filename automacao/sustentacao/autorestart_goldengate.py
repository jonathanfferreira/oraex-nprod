
import subprocess
import os
import argparse
import sys
import logging
import time

# Configuração Padrão
GGS_HOME_DEFAULT = "/ggs"
WAIT_AFTER_START_SECONDS = 10 # Tempo para esperar e conferir se o processo manteve-se UP

# Importar utils dinamicamente para poder rodar de qualquer lugar
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from automacao.utils.maintenance import MaintenanceManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_ggsci_command(ggs_home, command):
    """Executa um comando no ggsci e retorna a saída."""
    ggsci_path = os.path.join(ggs_home, "ggsci")
    
    if not os.path.exists(ggsci_path):
        logging.error(f"Executável ggsci não encontrado em {ggs_home}")
        return None

    try:
        process = subprocess.Popen(
            [ggsci_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=ggs_home
        )
        stdout, stderr = process.communicate(input=command + "\nexit\n")
        return stdout
    except Exception as e:
        logging.error(f"Erro ao executar ggsci: {e}")
        return None

def parse_abended_processes(output):
    """Retorna lista de dicionários com processos ABENDED ou STOPPED."""
    problems = []
    lines = output.splitlines()
    
    for line in lines:
        parts = line.split()
        if len(parts) >= 2:
            status = parts[1].upper()
            program = parts[0].upper()
            
            if program in ["PROGRAM", "GGS", "ORACLE"]: 
                continue

            if status in ["ABENDED", "STOPPED"]:
                group_name = parts[2] if len(parts) > 2 else "UNKNOWN"
                problems.append({
                    "program": program,
                    "group": group_name,
                    "status": status
                })
    return problems

def check_process_status(ggs_home, group_name):
    """Verifica o status de um processo específico."""
    output = run_ggsci_command(ggs_home, f"info {group_name}")
    if not output: return "UNKNOWN"
    
    for line in output.splitlines():
        if group_name.upper() in line.upper():
            parts = line.split()
            # Tenta achar o status na linha (geralmente 2a coluna)
            # Ex: EXTRACT    RUNNING     EXT1 ...
            for part in parts:
                if part in ["RUNNING", "ABENDED", "STOPPED", "STARTING"]:
                    return part
    return "UNKNOWN"

def attempt_restart(ggs_home, process):
    """Tenta reiniciar o processo e valida se ficou UP."""
    group = process['group']
    logging.info(f"⚡ Tentando Auto-Restart do processo: {group} ({process['program']})")
    
    # 1. Comando de Start
    run_ggsci_command(ggs_home, f"start {group}")
    
    # 2. Espera de Segurança (Warm-up)
    logging.info(f"⏳ Aguardando {WAIT_AFTER_START_SECONDS}s para validar estabilidade...")
    time.sleep(WAIT_AFTER_START_SECONDS)
    
    # 3. Validação Pós-Restart
    new_status = check_process_status(ggs_home, group)
    logging.info(f"Status pós-restart de {group}: {new_status}")
    
    if new_status == "RUNNING":
        logging.info(f"✅ SUCESSO: Processo {group} recuperado automaticamente!")
        return True
    else:
        logging.warning(f"❌ FALHA: Processo {group} continua {new_status} após tentativa de restart.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Oracle GoldenGate Auto-Restart Bot 🤖")
    parser.add_argument("--home", default=GGS_HOME_DEFAULT, help="Caminho do Oracle GoldenGate Home")
    parser.add_argument("--dry-run", action="store_true", help="Simula mas não executa o start")
    args = parser.parse_args()

    logging.info(f"Analisando GoldenGate em: {args.home}")
    
    # 0. Safety Check - Maintenance Mode
    if MaintenanceManager.is_active():
        sys.exit(0) # Sai limpo, sem erro, pois é comportamento esperado

    output = run_ggsci_command(args.home, "info all")
    if not output:
        logging.error("Falha ao comunicar com GGSCI.")
        sys.exit(1)

    abended = parse_abended_processes(output)
    
    if not abended:
        logging.info("Tudo limpo. Nenhum processo ABENDED. 🍃")
        sys.exit(0)

    logging.info(f"Detectados {len(abended)} processos parados. Iniciando protocolos de recuperação.")
    
    failed_recoveries = []
    
    for proc in abended:
        if args.dry_run:
            logging.info(f"[DRY-RUN] Reiniciaria {proc['group']}")
            continue
            
        success = attempt_restart(args.home, proc)
        if not success:
            failed_recoveries.append(proc['group'])

    if failed_recoveries:
        print(f"\n🚨 AVISO AO NOC: Automação falhou em recuperar: {', '.join(failed_recoveries)}")
        print("Ação Humana Obrigatória: Investigar ggserr.log e report file do processo.")
        sys.exit(1) # Exit code 1 para o Zabbix saber que ainda tem problema
    else:
        print("✅ Todos os incidentes foram tratados automaticamente.")
        sys.exit(0)

if __name__ == "__main__":
    main()
