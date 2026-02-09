#!/usr/bin/env python3
"""
Teste de Conexão MongoDB Local
-------------------------------
Testa conexão com MongoDB em container Docker
"""
import sys
import os

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from pymongo import MongoClient
    print("✅ pymongo importado com sucesso")
except ImportError:
    print("❌ pymongo não encontrado. Instale: pip install pymongo")
    sys.exit(1)

def test_connection():
    """Testa conexão com MongoDB"""
    print("\n🔌 Testando conexão MongoDB...")
    
    # Credenciais do container
    connection_string = "mongodb://admin:admin123@localhost:27017/"
    
    try:
        print(f"   Conectando em: localhost:27017")
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        
        # Testar conexão
        client.admin.command('ping')
        print("✅ Conexão estabelecida!")
        
        # Obter informações do servidor
        server_info = client.server_info()
        print(f"   Versão MongoDB: {server_info['version']}")
        
        # Listar databases
        databases = client.list_database_names()
        print(f"   Databases: {databases}")
        
        # Testar operação básica
        db = client.test_db
        collection = db.test_collection
        result = collection.insert_one({"test": "data", "timestamp": "2026-02-02"})
        print(f"   Documento inserido: {result.inserted_id}")
        
        # Limpar
        collection.delete_one({"_id": result.inserted_id})
        client.close()
        
        print("✅ Teste de conexão concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        print("   Verifique se o container MongoDB está rodando:")
        print("   docker-compose -f docker-compose.test.yml ps")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
