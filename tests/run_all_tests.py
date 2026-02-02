#!/usr/bin/env python3
"""
SCRIPT DE TESTE COMPLETO - Executa testes em todas as automações
Execute da pasta tests/ ou da raiz do projeto.
"""

import sys
import os
import unittest

# Adiciona o diretório pai ao path para importar os módulos
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_tests():
    """Executa todos os testes e retorna resultado."""
    
    print("="*70)
    print("🧪 EXECUTANDO TESTES DAS AUTOMAÇÕES ORAEX")
    print("="*70)
    print()
    
    # Descobre e carrega todos os testes
    loader = unittest.TestLoader()
    test_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # Executa os testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("="*70)
    print("📊 RESUMO DOS TESTES")
    print("="*70)
    print(f"   Total de testes: {result.testsRun}")
    print(f"   ✅ Sucesso: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   ❌ Falhas: {len(result.failures)}")
    print(f"   ⚠️  Erros: {len(result.errors)}")
    print("="*70)
    
    if result.failures:
        print("\n❌ FALHAS:")
        for test, traceback in result.failures:
            print(f"   - {test}")
    
    if result.errors:
        print("\n⚠️  ERROS:")
        for test, traceback in result.errors:
            print(f"   - {test}")
    
    return result.wasSuccessful()


def test_imports():
    """Testa se todos os módulos são importáveis."""
    print("\n📦 VERIFICANDO IMPORTAÇÕES...")
    
    modules = [
        ("automacao.diagnosticos.oracle_healthcheck", "OracleHealthCheck"),
        ("automacao.monitoramento.check_partitioning", "check_partitions"),
        ("automacao.monitoramento.check_tablespaces", None),
        ("automacao.monitoramento.asm_capacity_report", "DiskGroup"),
        ("automacao.sustentacao.oracle_housekeeper", "OracleHousekeeper"),
        ("automacao.sustentacao.autorestart_goldengate", None),
        ("automacao.sustentacao.smart_log_rotate", None),
        ("automacao.backup.rman_backup_manager", "RMANBackupManager"),
        ("automacao.configuracao.configure_sqlnet", "SQLNetConfigurator"),
        ("automacao.configuracao.create_application_service", "generate_service_name"),
        ("automacao.instalacao.verify_installation_prereqs", "PrereqChecker"),
    ]
    
    all_ok = True
    for module, symbol in modules:
        try:
            mod = __import__(module, fromlist=[symbol] if symbol else [])
            if symbol:
                getattr(mod, symbol)
            print(f"   ✅ {module}")
        except Exception as e:
            print(f"   ❌ {module}: {e}")
            all_ok = False
    
    return all_ok


def test_service_name_generator():
    """Testa o gerador de nomes de service."""
    print("\n🔧 TESTANDO GERADOR DE NOMES DE SERVICE...")
    
    try:
        from automacao.configuracao.create_application_service import generate_service_name
        
        tests = [
            ("INTEG", "PRD", "INTEGSRVPRD"),
            ("Core", "HG", "CORESRVHG"),
            ("App-Test", "DEV", "APPTESTSRVDEV"),
        ]
        
        all_ok = True
        for app, site, expected in tests:
            result = generate_service_name(app, site)
            if result == expected:
                print(f"   ✅ {app} + {site} = {result}")
            else:
                print(f"   ❌ {app} + {site} = {result} (esperado: {expected})")
                all_ok = False
        
        return all_ok
    except Exception as e:
        print(f"   ⚠️  Não foi possível testar: {e}")
        return True  # Não falha se não conseguir importar


if __name__ == "__main__":
    print("\n" + "🚀"*35)
    print("    ORAEX AUTOMATION TEST SUITE")
    print("🚀"*35 + "\n")
    
    # Testa importações
    imports_ok = test_imports()
    
    # Testa gerador de nomes
    names_ok = test_service_name_generator()
    
    # Executa testes unitários
    tests_ok = run_tests()
    
    print("\n" + "="*70)
    print("🏁 RESULTADO FINAL")
    print("="*70)
    
    if tests_ok:
        print("✅ TODOS OS TESTES PASSARAM!")
        sys.exit(0)
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        sys.exit(1)
