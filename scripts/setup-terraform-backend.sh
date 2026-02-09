#!/bin/bash
# ==============================================================================
# Script: Configurar Backend Remoto Terraform (S3 + DynamoDB)
# ==============================================================================
# Este script configura o backend remoto para o Terraform na AWS
# Uso: ./setup-terraform-backend.sh <bucket-name> <region>
# ==============================================================================

set -e

BUCKET_NAME=${1:-"getnet-terraform-state"}
REGION=${2:-"us-east-1"}
DYNAMODB_TABLE="terraform-state-lock"

echo "🚀 Configurando backend Terraform remoto..."
echo "   Bucket: ${BUCKET_NAME}"
echo "   Region: ${REGION}"
echo ""

# Verificar se AWS CLI está instalado
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI não encontrado. Instale: https://aws.amazon.com/cli/"
    exit 1
fi

# Criar bucket S3
echo "📦 Criando bucket S3..."
aws s3 mb s3://${BUCKET_NAME} --region ${REGION} 2>/dev/null || echo "   Bucket já existe ou erro de permissão"

# Habilitar versionamento
echo "   Habilitando versionamento..."
aws s3api put-bucket-versioning \
    --bucket ${BUCKET_NAME} \
    --versioning-configuration Status=Enabled

# Habilitar criptografia
echo "   Habilitando criptografia..."
aws s3api put-bucket-encryption \
    --bucket ${BUCKET_NAME} \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'

# Bloquear acesso público
echo "   Bloqueando acesso público..."
aws s3api put-public-access-block \
    --bucket ${BUCKET_NAME} \
    --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Criar tabela DynamoDB para lock
echo "🔒 Criando tabela DynamoDB para lock..."
aws dynamodb create-table \
    --table-name ${DYNAMODB_TABLE} \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region ${REGION} \
    2>/dev/null || echo "   Tabela já existe"

echo ""
echo "✅ Backend configurado com sucesso!"
echo ""
echo "📝 Próximos passos:"
echo "   1. Configure o backend no Terraform:"
echo "      cd infra/terraform/environments/production"
echo "      terraform init -backend-config=backend.hcl"
echo ""
echo "   2. Crie o arquivo backend.hcl:"
echo "      bucket         = \"${BUCKET_NAME}\""
echo "      key            = \"oraex/terraform.tfstate\""
echo "      region         = \"${REGION}\""
echo "      dynamodb_table = \"${DYNAMODB_TABLE}\""
echo "      encrypt        = true"
