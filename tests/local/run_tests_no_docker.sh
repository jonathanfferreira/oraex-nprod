#!/bin/bash
# ==============================================================================
# Script: Executar Testes Sem Docker (Linux/Mac)
# ==============================================================================
# Executa testes que não precisam de Docker
# ==============================================================================

echo "================================================================================"
echo "TESTES SEM DOCKER - ORAEX"
echo "================================================================================"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale Python 3.8 ou superior."
    exit 1
fi

echo "✅ Python encontrado"
echo ""

# Executar testes
echo "Executando testes sem Docker..."
echo ""

python3 tests/local/test_without_docker.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Todos os testes passaram!"
    echo ""
    echo "💡 Próximos passos:"
    echo "   - Execute testes unitários: python -m pytest tests/ -v"
    echo "   - Valide automações com mocks"
    echo "   - Quando possível, teste com Docker ou ambiente real"
    exit 0
else
    echo ""
    echo "⚠️  Alguns testes falharam"
    exit 1
fi
