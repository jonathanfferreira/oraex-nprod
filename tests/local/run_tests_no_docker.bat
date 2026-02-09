@echo off
REM ==============================================================================
REM Script: Executar Testes Sem Docker (Windows)
REM ==============================================================================
REM Executa testes que não precisam de Docker
REM ==============================================================================

echo ================================================================================
echo TESTES SEM DOCKER - ORAEX
echo ================================================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale Python 3.8 ou superior.
    pause
    exit /b 1
)

echo [OK] Python encontrado
echo.

REM Executar testes
echo Executando testes sem Docker...
echo.

python tests/local/test_without_docker.py

if errorlevel 1 (
    echo.
    echo [ERRO] Alguns testes falharam
    pause
    exit /b 1
) else (
    echo.
    echo [OK] Todos os testes passaram!
    echo.
    echo Proximos passos:
    echo   - Execute testes unitarios: python -m pytest tests/ -v
    echo   - Valide automacoes com mocks
    echo   - Quando possivel, teste com Docker ou ambiente real
    pause
)
