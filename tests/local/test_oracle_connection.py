#!/usr/bin/env python3
"""
Teste de Conexão Oracle Local
------------------------------
Testa conexão com Oracle em container Docker
"""
import sys
import os

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    import cx_Oracle
    print("✅ cx_Oracle importado com sucesso")
except ImportError:
    print("❌ cx_Oracle não encontrado. Instale: pip install cx_Oracle")
    sys.exit(1)

def test_connection():
    """Testa conexão com Oracle"""
    print("\n🔌 Testando conexão Oracle...")
    
    # Credenciais do container
    username = "system"
    password = "Oracle123!"
    dsn = "localhost:1521/XE"
    
    try:
        print(f"   Conectando em: {dsn}")
        connection = cx_Oracle.connect(username, password, dsn, encoding="UTF-8")
        print("✅ Conexão estabelecida!")
        
        # Testar query
        cursor = connection.cursor()
        cursor.execute("SELECT banner FROM v$version WHERE rownum=1")
        version = cursor.fetchone()[0]
        print(f"   Versão Oracle: {version}")
        
        # Testar instância
        cursor.execute("SELECT instance_name, status FROM v$instance")
        instance = cursor.fetchone()
        print(f"   Instância: {instance[0]} - Status: {instance[1]}")
        
        cursor.close()
        connection.close()
        
        print("✅ Teste de conexão concluído com sucesso!")
        return True
        
    except cx_Oracle.Error as e:
        error, = e.args
        print(f"❌ Erro ao conectar: {error.message}")
        print(f"   Código: {error.code}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
