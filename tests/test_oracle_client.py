import sys
import os

print("="*60)
print("TESTE DE CONEXÃO ORACLE (cx_Oracle)")
print("="*60)

print(f"Python Version: {sys.version}")
print(f"Architecture: {'64-bit' if sys.maxsize > 2**32 else '32-bit'}")

try:
    import cx_Oracle
    print(f"cx_Oracle Version: {cx_Oracle.version}")
    
    # Tenta inicializar o client sem argumentos primeiro (usa PATH)
    try:
        cx_Oracle.init_oracle_client()
        print("✅ Oracle Client inicializado via PATH!")
    except Exception as e:
        print(f"⚠️  Falha ao carregar via PATH: {e}")
        
        # Tenta procurar em locais comuns
        common_paths = [
            r"C:\oracle\instantclient_19_19",
            r"C:\instantclient_19_19",
            r"C:\oracle\instantclient_21_10"
        ]
        
        found = False
        for path in common_paths:
            if os.path.exists(path):
                print(f"🔍 Tentando path conhecido: {path}")
                try:
                    cx_Oracle.init_oracle_client(lib_dir=path)
                    print(f"✅ Sucesso com lib_dir='{path}'")
                    found = True
                    break
                except Exception as ex:
                    print(f"   Falha: {ex}")
        
        if not found:
            print("\n❌ CRÍTICO: Não foi possível carregar a biblioteca do Oracle Client.")
            print("Verifique se o Instant Client está baixado e no PATH do Windows.")

except ImportError:
    print("❌ ERRO: Módulo 'cx_Oracle' não instalado.")
    print(">> Execute: pip install cx_Oracle")

print("="*60)
