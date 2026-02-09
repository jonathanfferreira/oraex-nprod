"""
ORAEX - Packaging Script
------------------------
Empacota a solução ORAEX para deploy em ambiente Getnet.
Gera um arquivo .zip contendo apenas o necessário para produção.

Uso:
    python run_packaging.py
"""
import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# Configuração
# Se rodando da raiz do projeto (d:\antigravity\oraex\nprod)
BASE_DIR = Path.cwd()
if (BASE_DIR / "nprod").exists():
    BASE_DIR = BASE_DIR / "nprod"
elif (BASE_DIR / "oraex").exists(): # Caso esteja um nivel acima
     BASE_DIR = BASE_DIR / "oraex" / "nprod"

DIST_DIR = BASE_DIR / "dist"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")
ZIP_NAME = f"oraex_deploy_getnet_{TIMESTAMP}.zip"

# O que incluir no pacote
INCLUDE_DIRS = [
    "automacao",
    "dashboard",
    "docs",
    "infra/ansible",
    "presentation_site"
]

INCLUDE_FILES = [
    "README.md",
    "requirements.txt",
    "walkthrough.md",
    "presentation.html"
]

EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    ".git",
    ".vscode",
    "tests",      # Testes não vão para produção geralmente, ou vão em pacote separado
    "venv",
    ".env",
    "dist"
]

def create_dist_dir():
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir()

def is_excluded(path: Path) -> bool:
    for pattern in EXCLUDE_PATTERNS:
        if pattern in str(path) or path.match(pattern):
            return True
    return False

def zip_project():
    zip_path = DIST_DIR / ZIP_NAME
    print(f"📦 Criando pacote: {zip_path}")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Adicionar pastas
        for dir_name in INCLUDE_DIRS:
            src_path = BASE_DIR / dir_name
            if not src_path.exists():
                print(f"⚠️  Diretório não encontrado: {dir_name}")
                continue

            for root, dirs, files in os.walk(src_path):
                # Filtrar diretórios excluídos in-place
                dirs[:] = [d for d in dirs if d not in EXCLUDE_PATTERNS and not d.startswith('.')]
                
                for file in files:
                    file_path = Path(root) / file
                    if is_excluded(file_path):
                        continue
                        
                    arcname = file_path.relative_to(BASE_DIR)
                    zipf.write(file_path, arcname)
                    print(f"  + {arcname}")

        # Adicionar arquivos soltos
        for file_name in INCLUDE_FILES:
            file_path = BASE_DIR / file_name
            if file_path.exists():
                zipf.write(file_path, file_name)
                print(f"  + {file_name}")

    print(f"\n✅ Pacote criado com sucesso: {zip_path}")
    print(f"   Tamanho: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    create_dist_dir()
    zip_project()
