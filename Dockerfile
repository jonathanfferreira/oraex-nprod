# ORAEX Automation Stack
# ======================
# Container com todos os scripts de automação Oracle
# Pronto para deploy em qualquer ambiente com Python

FROM python:3.9-slim-bookworm

LABEL maintainer="Jonathan Ferreira"
LABEL project="ORAEX-NPROD"
LABEL description="Oracle Automation & Self-Healing Stack"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV ORACLE_DSN="localhost/orcl"
ENV ORACLE_USER="system"
ENV ORACLE_PASSWORD="oracle"
ENV WEBHOOK_PORT=5001

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    libaio1 \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Criar diretórios
WORKDIR /app
RUN mkdir -p /app/automacao /app/observability /app/logs

# Copiar requirements primeiro (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY automacao/ /app/automacao/
COPY observability/ /app/observability/
COPY scripts/webhook_receiver.py /app/

# Expor porta do webhook
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5001/health')" || exit 1

# Variável de ambiente para localizar os módulos
ENV ORAEX_HOME=/app

# Comando padrão: iniciar webhook receiver com gunicorn
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5001", "--timeout", "300", "webhook_receiver:app"]
