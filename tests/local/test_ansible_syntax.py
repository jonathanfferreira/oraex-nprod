#!/usr/bin/env python3
"""
Teste de Sintaxe Ansible
-------------------------
Valida sintaxe de playbooks e roles Ansible
"""
import subprocess
import sys
import os
import glob

def test_ansible_syntax(file_path):
    """Testa sintaxe de um arquivo Ansible"""
    try:
        result = subprocess.run(
            ["ansible-playbook", "--syntax-check", file_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    """Executa testes de sintaxe"""
    print("="*70)
    print("🧪 TESTES DE SINTAXE ANSIBLE")
    print("="*70)
    print()
    
    # Verificar se Ansible está instalado
    try:
        result = subprocess.run(
            ["ansible-playbook", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ Ansible encontrado: {version}")
        else:
            print("❌ Ansible não encontrado. Instale: pip install ansible")
            return False
    except FileNotFoundError:
        print("❌ Ansible não encontrado. Instale: pip install ansible")
        return False
    
    print()
    
    # Encontrar todos os playbooks
    playbooks = []
    playbooks.extend(glob.glob("infra/ansible/playbooks/*.yml"))
    playbooks.extend(glob.glob("infra/ansible/playbooks/*.yaml"))
    
    # Encontrar tasks em roles
    role_tasks = []
    for root, dirs, files in os.walk("infra/ansible/roles"):
        for file in files:
            if file.endswith(('.yml', '.yaml')):
                role_tasks.append(os.path.join(root, file))
    
    all_files = playbooks + role_tasks
    results = []
    
    print(f"📋 Encontrados {len(all_files)} arquivos para validar...")
    print()
    
    for file_path in all_files:
        print(f"   Validando: {file_path}")
        success, stdout, stderr = test_ansible_syntax(file_path)
        
        if success:
            print(f"      ✅ OK")
            results.append((file_path, True))
        else:
            print(f"      ❌ ERRO")
            if stderr:
                print(f"         {stderr[:100]}...")
            results.append((file_path, False))
    
    # Resumo
    print()
    print("="*70)
    print("📊 RESUMO")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    print(f"   ✅ Passou: {passed}")
    print(f"   ❌ Falhou: {failed}")
    print(f"   📊 Total: {len(results)}")
    
    if failed > 0:
        print("\n   Arquivos com erro:")
        for file_path, result in results:
            if not result:
                print(f"      - {file_path}")
    
    print()
    
    if failed == 0:
        print("✅ Todos os arquivos Ansible estão com sintaxe correta!")
        return True
    else:
        print(f"⚠️  {failed} arquivo(s) com erro de sintaxe")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
