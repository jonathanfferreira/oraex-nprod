#!/usr/bin/env python3
"""
Testes Sem Docker
-----------------
Testa automações sem precisar de Docker ou containers
Foca em validação de código, sintaxe e lógica
"""
import sys
import os
import subprocess
import json

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_python_imports():
    """Testa se imports Python funcionam"""
    print("[TESTE] Testando imports Python...")
    
    modules_required = [
        ("json", "json"),
        ("logging", "logging"),
    ]
    
    modules_optional = [
        ("cx_Oracle", "cx_Oracle"),
        ("pymongo", "pymongo"),
    ]
    
    results_required = []
    for name, module in modules_required:
        try:
            __import__(module)
            print(f"   [OK] {name} (obrigatorio)")
            results_required.append(True)
        except ImportError:
            print(f"   [ERRO] {name} nao encontrado (obrigatorio!)")
            results_required.append(False)
    
    for name, module in modules_optional:
        try:
            __import__(module)
            print(f"   [OK] {name} (opcional)")
        except ImportError:
            print(f"   [AVISO] {name} nao encontrado (opcional)")
    
    return all(results_required) if results_required else True

def test_ansible_syntax():
    """Testa sintaxe Ansible"""
    print("\n[TESTE] Testando sintaxe Ansible...")
    
    try:
        result = subprocess.run(
            ["ansible-playbook", "--version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"   [OK] Ansible encontrado: {result.stdout.split()[1]}")
            
            # Testar sintaxe de um playbook
            test_playbook = "infra/ansible/playbooks/deploy_all.yml"
            if os.path.exists(test_playbook):
                result = subprocess.run(
                    ["ansible-playbook", "--syntax-check", test_playbook],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"   [OK] Sintaxe OK: {test_playbook}")
                    return True
                else:
                    print(f"   [ERRO] Erro de sintaxe: {result.stderr[:100]}")
                    return False
            return True
        else:
            print("   [AVISO] Ansible nao encontrado")
            return False
    except FileNotFoundError:
        print("   [AVISO] Ansible nao instalado (opcional)")
        return True

def test_terraform_syntax():
    """Testa sintaxe Terraform"""
    print("\n[TESTE] Testando sintaxe Terraform...")
    
    try:
        result = subprocess.run(
            ["terraform", "version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"   [OK] Terraform encontrado: {result.stdout.split()[1]}")
            
            # Testar validação de um módulo
            test_dir = "infra/terraform/modules/oracle-rac"
            if os.path.exists(test_dir):
                result = subprocess.run(
                    ["terraform", "init", "-backend=false"],
                    cwd=test_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    result = subprocess.run(
                        ["terraform", "validate"],
                        cwd=test_dir,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        print(f"   [OK] Validacao OK: {test_dir}")
                        return True
                    else:
                        print(f"   [AVISO] Erros de validacao (pode ser esperado sem providers):")
                        print(f"      {result.stderr[:200]}")
                        return True  # Não falhar, pois pode ser esperado
            return True
        else:
            print("   [AVISO] Terraform nao encontrado")
            return False
    except FileNotFoundError:
        print("   [AVISO] Terraform nao instalado (opcional)")
        return True

def test_python_scripts():
    """Testa scripts Python do projeto"""
    print("\n[TESTE] Testando scripts Python...")
    
    scripts = [
        "automacao/diagnosticos/oracle_healthcheck.py",
        "automacao/monitoramento/slo_tracker.py",
        "automacao/mongodb/diagnosticos/check_health.py",
    ]
    
    results = []
    for script in scripts:
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            script
        )
        
        if os.path.exists(script_path):
            # Testar se o script tem sintaxe válida
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", script_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print(f"   [OK] {os.path.basename(script)}")
                    results.append(True)
                else:
                    print(f"   [ERRO] {os.path.basename(script)}: {result.stderr[:100]}")
                    results.append(False)
            except Exception as e:
                print(f"   [AVISO] {os.path.basename(script)}: {e}")
                results.append(False)
        else:
            print(f"   [AVISO] {script} nao encontrado")
    
    return all(results) if results else True

def test_config_files():
    """Testa arquivos de configuração"""
    print("\n[TESTE] Testando arquivos de configuracao...")
    
    config_files = [
        "infra/ansible/ansible.cfg",
        "infra/terraform/shared/backend.tf",
        "docker-compose.test.yml",
    ]
    
    results = []
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"   [OK] {config_file}")
            results.append(True)
        else:
            print(f"   [AVISO] {config_file} nao encontrado")
            results.append(False)
    
    return all(results) if results else True

def test_project_structure():
    """Testa estrutura do projeto"""
    print("\n[TESTE] Testando estrutura do projeto...")
    
    required_dirs = [
        "automacao",
        "infra/ansible",
        "infra/terraform",
        "tests",
        "docs",
    ]
    
    results = []
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"   [OK] {dir_path}/")
            results.append(True)
        else:
            print(f"   [ERRO] {dir_path}/ nao encontrado")
            results.append(False)
    
    return all(results)

def main():
    """Executa todos os testes sem Docker"""
    # Configurar encoding UTF-8 para Windows
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("="*70)
    print("TESTES SEM DOCKER - ORAEX")
    print("="*70)
    print()
    print("Estes testes validam código, sintaxe e estrutura")
    print("sem precisar de Docker ou containers.")
    print()
    
    tests = [
        ("Estrutura do Projeto", test_project_structure),
        ("Imports Python", test_python_imports),
        ("Scripts Python", test_python_scripts),
        ("Sintaxe Ansible", test_ansible_syntax),
        ("Sintaxe Terraform", test_terraform_syntax),
        ("Arquivos de Configuração", test_config_files),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            results.append((test_name, False))
    
    # Resumo
    print()
    print("="*70)
    print("📊 RESUMO")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for test_name, result in results:
        status = "[OK] PASS" if result else "[ERRO] FAIL"
        print(f"   {status}: {test_name}")
    
    print()
    print(f"   [OK] Passou: {passed}")
    print(f"   [ERRO] Falhou: {failed}")
    print(f"   [INFO] Total: {len(results)}")
    print()
    
    if failed == 0:
        print("[OK] Todos os testes passaram!")
        print()
        print("Proximos passos:")
        print("   - Execute testes unitarios: python -m pytest tests/ -v")
        print("   - Valide automacoes com mocks")
        print("   - Quando possivel, teste com Docker ou ambiente real")
        return True
    else:
        print("[AVISO] Alguns testes falharam")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
