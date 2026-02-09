#!/usr/bin/env python3
"""
ORAEX Build Script
==================
Script para facilitar o build do projeto ORAEX.
Suporta Docker e PyInstaller.

Uso:
    python build.py docker      # Build Docker image
    python build.py pyinstaller # Build executáveis standalone
    python build.py all         # Build ambos
"""
import subprocess
import sys
import os
import shutil

PROJECT_NAME = "oraex-automation"
VERSION = "1.0.0"

def run_cmd(cmd: list, check: bool = True):
    """Executa comando e mostra output."""
    print(f"\n{'='*60}")
    print(f"$ {' '.join(cmd)}")
    print('='*60)
    result = subprocess.run(cmd, check=check)
    return result.returncode == 0

def build_docker():
    """Build Docker image."""
    print("\n🐳 Building Docker Image...")
    
    # Build image
    success = run_cmd([
        "docker", "build",
        "-t", f"{PROJECT_NAME}:{VERSION}",
        "-t", f"{PROJECT_NAME}:latest",
        "."
    ])
    
    if success:
        print(f"\n✅ Docker image '{PROJECT_NAME}:{VERSION}' built successfully!")
        print("\nPara rodar:")
        print(f"  docker run -p 5001:5001 {PROJECT_NAME}:latest")
    else:
        print("\n❌ Failed to build Docker image")
    
    return success

def build_pyinstaller():
    """Build executáveis com PyInstaller."""
    print("\n📦 Building Standalone Executables...")
    
    # Verificar se PyInstaller está instalado
    try:
        import PyInstaller
    except ImportError:
        print("⚠️ PyInstaller não encontrado. Instalando...")
        run_cmd([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Limpar builds anteriores
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    
    # Build
    success = run_cmd([sys.executable, "-m", "PyInstaller", "oraex.spec"])
    
    if success:
        print(f"\n✅ Executables built successfully!")
        print(f"\nArquivos em: ./dist/")
        if os.path.exists("dist"):
            for f in os.listdir("dist"):
                print(f"  - {f}")
    else:
        print("\n❌ Failed to build executables")
    
    return success

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    
    action = sys.argv[1].lower()
    
    if action == "docker":
        return 0 if build_docker() else 1
    elif action == "pyinstaller":
        return 0 if build_pyinstaller() else 1
    elif action == "all":
        docker_ok = build_docker()
        pyinstaller_ok = build_pyinstaller()
        
        print("\n" + "="*60)
        print("BUILD SUMMARY")
        print("="*60)
        print(f"  Docker:      {'✅' if docker_ok else '❌'}")
        print(f"  PyInstaller: {'✅' if pyinstaller_ok else '❌'}")
        
        return 0 if (docker_ok and pyinstaller_ok) else 1
    else:
        print(f"❌ Unknown action: {action}")
        print(__doc__)
        return 1

if __name__ == "__main__":
    sys.exit(main())
