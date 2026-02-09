#!/bin/bash
# ==============================================================================
# Script: Executar Todos os Testes Locais
# ==============================================================================
# Executa suite completa de testes locais
# ==============================================================================

set -e

echo "="*70
echo "🧪 SUITE DE TESTES LOCAIS - ORAEX"
echo "="*70
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contadores
PASSED=0
FAILED=0

# Função para executar teste
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -e "${YELLOW}▶ Executando: ${test_name}${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ ${test_name} - PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ ${test_name} - FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

# 1. Testes de sintaxe Ansible
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. TESTES DE SINTAXE ANSIBLE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
run_test "Sintaxe Ansible" "python3 tests/local/test_ansible_syntax.py"

# 2. Testes Terraform (validação)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. TESTES TERRAFORM (Validação)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
run_test "Terraform Plan" "python3 tests/local/test_terraform_plan.py"

# 3. Verificar se containers estão rodando
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. VERIFICAÇÃO DE CONTAINERS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v docker &> /dev/null; then
    if docker ps | grep -q oraex-; then
        echo -e "${GREEN}✅ Containers Docker estão rodando${NC}"
        ((PASSED++))
        
        # 4. Testes de conexão
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "4. TESTES DE CONEXÃO"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        run_test "Conexão Oracle" "python3 tests/local/test_oracle_connection.py"
        run_test "Conexão MongoDB" "python3 tests/local/test_mongodb_connection.py"
    else
        echo -e "${YELLOW}⚠️  Containers não estão rodando. Execute:${NC}"
        echo "   ./tests/local/test_local_setup.sh"
        echo "   ou"
        echo "   docker-compose -f docker-compose.test.yml up -d"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠️  Docker não encontrado. Pulando testes de conexão.${NC}"
fi

# 5. Testes Python unitários
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. TESTES UNITÁRIOS PYTHON"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v pytest &> /dev/null; then
    run_test "Testes Unitários" "python -m pytest tests/ -v --tb=short"
else
    echo -e "${YELLOW}⚠️  pytest não encontrado. Instale: pip install pytest${NC}"
fi

# Resumo final
echo ""
echo "="*70
echo "📊 RESUMO FINAL"
echo "="*70
echo -e "${GREEN}✅ Passou: ${PASSED}${NC}"
echo -e "${RED}❌ Falhou: ${FAILED}${NC}"
echo ""

TOTAL=$((PASSED + FAILED))
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 Todos os testes passaram!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Alguns testes falharam${NC}"
    exit 1
fi
