#!/bin/bash
# ==============================================================================
# Script: Setup de Ambiente de Testes Local
# ==============================================================================
# Configura ambiente local para testar automações sem infraestrutura real
# ==============================================================================

set -e

echo "🚀 Configurando ambiente de testes local ORAEX..."
echo ""

# Verificar dependências
echo "📋 Verificando dependências..."

command -v docker >/dev/null 2>&1 || { echo "❌ Docker não encontrado. Instale: https://www.docker.com/get-started"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose não encontrado."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 não encontrado."; exit 1; }

echo "✅ Dependências OK"
echo ""

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p tests/prometheus
mkdir -p tests/logs
mkdir -p tests/data
echo "✅ Diretórios criados"
echo ""

# Configurar Prometheus
echo "⚙️  Configurando Prometheus..."
cat > tests/prometheus/prometheus.yml <<EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'oraex-oracle'
    static_configs:
      - targets: ['host.docker.internal:9091']
  
  - job_name: 'oraex-mongodb'
    static_configs:
      - targets: ['host.docker.internal:9092']
EOF
echo "✅ Prometheus configurado"
echo ""

# Iniciar containers
echo "🐳 Iniciando containers Docker..."
docker-compose -f docker-compose.test.yml up -d

echo ""
echo "⏳ Aguardando serviços iniciarem..."
sleep 10

# Verificar saúde dos serviços
echo ""
echo "🏥 Verificando saúde dos serviços..."

check_service() {
    local service=$1
    local port=$2
    
    if nc -z localhost $port 2>/dev/null; then
        echo "✅ $service está rodando na porta $port"
    else
        echo "⚠️  $service não está respondendo na porta $port"
    fi
}

check_service "Oracle" 1521
check_service "MongoDB" 27017
check_service "PostgreSQL" 5432
check_service "Prometheus" 9090
check_service "Grafana" 3000

echo ""
echo "✅ Ambiente de testes configurado!"
echo ""
echo "📝 Próximos passos:"
echo "   1. Testar conexão Oracle:"
echo "      python tests/local/test_oracle_connection.py"
echo ""
echo "   2. Testar conexão MongoDB:"
echo "      python tests/local/test_mongodb_connection.py"
echo ""
echo "   3. Executar testes automatizados:"
echo "      python -m pytest tests/"
echo ""
echo "   4. Ver logs dos containers:"
echo "      docker-compose -f docker-compose.test.yml logs -f"
echo ""
echo "   5. Parar ambiente:"
echo "      docker-compose -f docker-compose.test.yml down"
