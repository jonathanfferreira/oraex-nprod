#!/usr/bin/env python3
"""
VERIFY_INSTALLATION_PREREQS.PY - Checklist Pré-Instalação Oracle 19c
=====================================================================
Automatiza a verificação de pré-requisitos antes de instalar Oracle.

Checagens:
- Pacotes RPM obrigatórios
- Parâmetros de Kernel (sysctl)
- Grupos/Usuários (oracle, dba, oinstall)
- Diretórios (/u01, /tmp com espaço)
- Swap e Memória

Uso:
  python verify_installation_prereqs.py
  python verify_installation_prereqs.py --json

Autor: ORAEX Automation Team
"""

import os
import sys
import argparse
import logging
import subprocess
import re
import json
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# RPMs obrigatórios para Oracle 19c no RHEL/OEL 7+
REQUIRED_RPMS = [
    "binutils", "compat-libcap1", "compat-libstdc++-33", "gcc", "gcc-c++",
    "glibc", "glibc-devel", "ksh", "libaio", "libaio-devel", "libgcc",
    "libstdc++", "libstdc++-devel", "libxcb", "libX11", "libXau", "libXi",
    "libXtst", "libXrender", "libXrender-devel", "make", "net-tools",
    "nfs-utils", "smartmontools", "sysstat", "unixODBC"
]

# Parâmetros de kernel obrigatórios (valores mínimos)
KERNEL_PARAMS = {
    "fs.file-max": 6815744,
    "kernel.sem": "250 32000 100 128",  # SEMMSL SEMMNS SEMOPM SEMMNI
    "kernel.shmmni": 4096,
    "kernel.shmall": 1073741824,  # Em pages (4KB cada)
    "kernel.shmmax": 4398046511104,  # 4TB
    "net.core.rmem_default": 262144,
    "net.core.rmem_max": 4194304,
    "net.core.wmem_default": 262144,
    "net.core.wmem_max": 1048576,
    "net.ipv4.ip_local_port_range": "9000 65500",
    "fs.aio-max-nr": 1048576
}

# Grupos obrigatórios
REQUIRED_GROUPS = ["oinstall", "dba", "oper", "backupdba", "dgdba", "kmdba", "asmdba"]

# Diretórios obrigatórios
REQUIRED_DIRS = {
    "/u01": {"min_gb": 50, "owner": "oracle", "group": "oinstall"},
    "/tmp": {"min_gb": 1, "owner": None, "group": None}
}


class PrereqChecker:
    """Verificador de pré-requisitos para instalação Oracle."""
    
    def __init__(self):
        self.results = {
            "rpms": {"status": "pending", "missing": [], "installed": []},
            "kernel": {"status": "pending", "issues": [], "ok": []},
            "groups": {"status": "pending", "missing": [], "ok": []},
            "users": {"status": "pending", "issues": []},
            "directories": {"status": "pending", "issues": [], "ok": []},
            "memory": {"status": "pending", "details": {}},
            "swap": {"status": "pending", "details": {}}
        }
    
    def _run_cmd(self, cmd: str) -> Tuple[int, str]:
        try:
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE, timeout=30)
            return result.returncode, result.stdout.decode('utf-8', errors='replace')
        except Exception as e:
            return -1, str(e)
    
    def check_rpms(self) -> bool:
        """Verifica pacotes RPM instalados."""
        logging.info("Verificando pacotes RPM...")
        
        # Lista todos os pacotes instalados
        rc, output = self._run_cmd("rpm -qa --queryformat '%{NAME}\n'")
        if rc != 0:
            self.results["rpms"]["status"] = "error"
            return False
        
        installed = set(output.strip().lower().splitlines())
        
        for rpm in REQUIRED_RPMS:
            # Verifica se o pacote (ignorando versão) está instalado
            if any(rpm.lower() in pkg for pkg in installed):
                self.results["rpms"]["installed"].append(rpm)
            else:
                self.results["rpms"]["missing"].append(rpm)
        
        self.results["rpms"]["status"] = "ok" if not self.results["rpms"]["missing"] else "fail"
        return self.results["rpms"]["status"] == "ok"
    
    def check_kernel_params(self) -> bool:
        """Verifica parâmetros de kernel."""
        logging.info("Verificando parâmetros de kernel...")
        
        for param, expected in KERNEL_PARAMS.items():
            rc, output = self._run_cmd(f"sysctl -n {param} 2>/dev/null")
            if rc != 0:
                self.results["kernel"]["issues"].append(f"{param}: não encontrado")
                continue
            
            current = output.strip()
            
            # Comparação básica (pode ser valor numérico ou string)
            if isinstance(expected, int):
                try:
                    if int(current.split()[0]) >= expected:
                        self.results["kernel"]["ok"].append(f"{param}={current}")
                    else:
                        self.results["kernel"]["issues"].append(
                            f"{param}: {current} (mínimo: {expected})")
                except ValueError:
                    self.results["kernel"]["issues"].append(f"{param}: valor inválido '{current}'")
            else:
                if current == expected:
                    self.results["kernel"]["ok"].append(f"{param}={current}")
                else:
                    self.results["kernel"]["issues"].append(
                        f"{param}: '{current}' (esperado: '{expected}')")
        
        self.results["kernel"]["status"] = "ok" if not self.results["kernel"]["issues"] else "fail"
        return self.results["kernel"]["status"] == "ok"
    
    def check_groups(self) -> bool:
        """Verifica grupos do sistema."""
        logging.info("Verificando grupos...")
        
        rc, output = self._run_cmd("cat /etc/group")
        if rc != 0:
            self.results["groups"]["status"] = "error"
            return False
        
        existing_groups = [line.split(":")[0] for line in output.splitlines()]
        
        for group in REQUIRED_GROUPS:
            if group in existing_groups:
                self.results["groups"]["ok"].append(group)
            else:
                self.results["groups"]["missing"].append(group)
        
        self.results["groups"]["status"] = "ok" if not self.results["groups"]["missing"] else "fail"
        return self.results["groups"]["status"] == "ok"
    
    def check_oracle_user(self) -> bool:
        """Verifica usuário oracle."""
        logging.info("Verificando usuário oracle...")
        
        rc, output = self._run_cmd("id oracle 2>/dev/null")
        if rc != 0:
            self.results["users"]["status"] = "fail"
            self.results["users"]["issues"].append("Usuário 'oracle' não existe")
            return False
        
        # Verifica grupos do usuário
        if "oinstall" not in output:
            self.results["users"]["issues"].append("oracle não pertence ao grupo oinstall")
        if "dba" not in output:
            self.results["users"]["issues"].append("oracle não pertence ao grupo dba")
        
        self.results["users"]["status"] = "ok" if not self.results["users"]["issues"] else "fail"
        self.results["users"]["details"] = output.strip()
        return self.results["users"]["status"] == "ok"
    
    def check_directories(self) -> bool:
        """Verifica diretórios obrigatórios."""
        logging.info("Verificando diretórios...")
        
        for dir_path, reqs in REQUIRED_DIRS.items():
            if not os.path.isdir(dir_path):
                self.results["directories"]["issues"].append(f"{dir_path}: não existe")
                continue
            
            # Verifica espaço disponível
            try:
                stat = os.statvfs(dir_path)
                free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
                
                if free_gb < reqs["min_gb"]:
                    self.results["directories"]["issues"].append(
                        f"{dir_path}: {free_gb:.1f}GB livre (mínimo: {reqs['min_gb']}GB)")
                else:
                    self.results["directories"]["ok"].append(f"{dir_path}: {free_gb:.1f}GB livre")
            except Exception as e:
                self.results["directories"]["issues"].append(f"{dir_path}: erro ao verificar - {e}")
        
        self.results["directories"]["status"] = "ok" if not self.results["directories"]["issues"] else "fail"
        return self.results["directories"]["status"] == "ok"
    
    def check_memory(self) -> bool:
        """Verifica memória disponível."""
        logging.info("Verificando memória...")
        
        try:
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()
            
            total_kb = int(re.search(r"MemTotal:\s+(\d+)", meminfo).group(1))
            free_kb = int(re.search(r"MemAvailable:\s+(\d+)", meminfo).group(1))
            
            total_gb = total_kb / (1024**2)
            free_gb = free_kb / (1024**2)
            
            self.results["memory"]["details"] = {
                "total_gb": round(total_gb, 2),
                "available_gb": round(free_gb, 2)
            }
            
            # Oracle 19c requer mínimo 8GB RAM
            if total_gb < 8:
                self.results["memory"]["status"] = "fail"
                self.results["memory"]["issue"] = f"Mínimo 8GB RAM (atual: {total_gb:.1f}GB)"
            else:
                self.results["memory"]["status"] = "ok"
                
        except Exception as e:
            self.results["memory"]["status"] = "error"
            self.results["memory"]["error"] = str(e)
            return False
        
        return self.results["memory"]["status"] == "ok"
    
    def check_swap(self) -> bool:
        """Verifica espaço de swap."""
        logging.info("Verificando swap...")
        
        try:
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()
            
            swap_total = int(re.search(r"SwapTotal:\s+(\d+)", meminfo).group(1))
            mem_total = int(re.search(r"MemTotal:\s+(\d+)", meminfo).group(1))
            
            swap_gb = swap_total / (1024**2)
            mem_gb = mem_total / (1024**2)
            
            self.results["swap"]["details"] = {"swap_gb": round(swap_gb, 2), "ram_gb": round(mem_gb, 2)}
            
            # Regra Oracle: RAM <= 16GB -> Swap = RAM; RAM > 16GB -> Swap = 16GB
            required_swap = min(mem_gb, 16)
            
            if swap_gb < required_swap:
                self.results["swap"]["status"] = "fail"
                self.results["swap"]["issue"] = f"Swap insuficiente: {swap_gb:.1f}GB (mínimo: {required_swap:.1f}GB)"
            else:
                self.results["swap"]["status"] = "ok"
                
        except Exception as e:
            self.results["swap"]["status"] = "error"
            return False
        
        return self.results["swap"]["status"] == "ok"
    
    def run_all(self) -> Dict:
        """Executa todas as verificações."""
        self.check_rpms()
        self.check_kernel_params()
        self.check_groups()
        self.check_oracle_user()
        self.check_directories()
        self.check_memory()
        self.check_swap()
        return self.results


def print_report(results: Dict):
    """Imprime relatório formatado."""
    print("\n" + "="*70)
    print("RELATÓRIO DE PRÉ-REQUISITOS - ORACLE 19c")
    print("="*70)
    
    status_icons = {"ok": "✅", "fail": "❌", "error": "⚠️", "pending": "⏳"}
    
    # RPMs
    print(f"\n📦 PACOTES RPM: {status_icons.get(results['rpms']['status'], '?')}")
    if results['rpms']['missing']:
        print(f"   Faltando ({len(results['rpms']['missing'])}):")
        for rpm in results['rpms']['missing'][:10]:
            print(f"      - {rpm}")
        if len(results['rpms']['missing']) > 10:
            print(f"      ... e mais {len(results['rpms']['missing']) - 10}")
    print(f"   Instalados: {len(results['rpms']['installed'])}/{len(REQUIRED_RPMS)}")
    
    # Kernel
    print(f"\n⚙️  PARÂMETROS KERNEL: {status_icons.get(results['kernel']['status'], '?')}")
    if results['kernel']['issues']:
        for issue in results['kernel']['issues'][:5]:
            print(f"   ❌ {issue}")
    print(f"   OK: {len(results['kernel']['ok'])}/{len(KERNEL_PARAMS)}")
    
    # Grupos
    print(f"\n👥 GRUPOS: {status_icons.get(results['groups']['status'], '?')}")
    if results['groups']['missing']:
        print(f"   Faltando: {', '.join(results['groups']['missing'])}")
    
    # Usuário
    print(f"\n👤 USUÁRIO ORACLE: {status_icons.get(results['users']['status'], '?')}")
    if results['users'].get('issues'):
        for issue in results['users']['issues']:
            print(f"   ❌ {issue}")
    
    # Diretórios
    print(f"\n📁 DIRETÓRIOS: {status_icons.get(results['directories']['status'], '?')}")
    for ok in results['directories']['ok']:
        print(f"   ✅ {ok}")
    for issue in results['directories']['issues']:
        print(f"   ❌ {issue}")
    
    # Memória
    print(f"\n💾 MEMÓRIA: {status_icons.get(results['memory']['status'], '?')}")
    if results['memory'].get('details'):
        d = results['memory']['details']
        print(f"   Total: {d.get('total_gb', 'N/A')} GB | Disponível: {d.get('available_gb', 'N/A')} GB")
    
    # Swap
    print(f"\n💿 SWAP: {status_icons.get(results['swap']['status'], '?')}")
    if results['swap'].get('details'):
        print(f"   Swap: {results['swap']['details'].get('swap_gb', 'N/A')} GB")
    
    # Resumo
    print("\n" + "="*70)
    all_ok = all(r.get('status') == 'ok' for r in results.values())
    if all_ok:
        print("✅ SISTEMA PRONTO PARA INSTALAÇÃO ORACLE 19c!")
    else:
        fails = sum(1 for r in results.values() if r.get('status') == 'fail')
        print(f"❌ {fails} PROBLEMA(S) ENCONTRADO(S) - CORRIJA ANTES DE INSTALAR")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(description="Verifica pré-requisitos Oracle 19c")
    parser.add_argument("--json", action="store_true", help="Saída em JSON")
    args = parser.parse_args()
    
    checker = PrereqChecker()
    results = checker.run_all()
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_report(results)


if __name__ == "__main__":
    main()
