# ==============================================================================
# Script: Configurar Backend Remoto Terraform (S3 + DynamoDB) - PowerShell
# ==============================================================================
# Este script configura o backend remoto para o Terraform na AWS
# Uso: .\setup-terraform-backend.ps1 -BucketName "getnet-terraform-state" -Region "us-east-1"
# ==============================================================================

param(
    [string]$BucketName = "getnet-terraform-state",
    [string]$Region = "us-east-1"
)

$DynamoDBTable = "terraform-state-lock"

Write-Host "🚀 Configurando backend Terraform remoto..." -ForegroundColor Cyan
Write-Host "   Bucket: $BucketName" -ForegroundColor Gray
Write-Host "   Region: $Region" -ForegroundColor Gray
Write-Host ""

# Verificar se AWS CLI está instalado
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI não encontrado. Instale: https://aws.amazon.com/cli/" -ForegroundColor Red
    exit 1
}

# Criar bucket S3
Write-Host "📦 Criando bucket S3..." -ForegroundColor Yellow
try {
    aws s3 mb "s3://$BucketName" --region $Region 2>$null
    Write-Host "   ✅ Bucket criado" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Bucket já existe ou erro de permissão" -ForegroundColor Yellow
}

# Habilitar versionamento
Write-Host "   Habilitando versionamento..." -ForegroundColor Gray
aws s3api put-bucket-versioning `
    --bucket $BucketName `
    --versioning-configuration Status=Enabled

# Habilitar criptografia
Write-Host "   Habilitando criptografia..." -ForegroundColor Gray
$encryptionConfig = @{
    Rules = @(
        @{
            ApplyServerSideEncryptionByDefault = @{
                SSEAlgorithm = "AES256"
            }
        }
    )
} | ConvertTo-Json -Compress

aws s3api put-bucket-encryption `
    --bucket $BucketName `
    --server-side-encryption-configuration $encryptionConfig

# Bloquear acesso público
Write-Host "   Bloqueando acesso público..." -ForegroundColor Gray
aws s3api put-public-access-block `
    --bucket $BucketName `
    --public-access-block-configuration `
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Criar tabela DynamoDB para lock
Write-Host "🔒 Criando tabela DynamoDB para lock..." -ForegroundColor Yellow
try {
    aws dynamodb create-table `
        --table-name $DynamoDBTable `
        --attribute-definitions AttributeName=LockID,AttributeType=S `
        --key-schema AttributeName=LockID,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --region $Region 2>$null
    Write-Host "   ✅ Tabela criada" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Tabela já existe" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Backend configurado com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Próximos passos:" -ForegroundColor Cyan
Write-Host "   1. Configure o backend no Terraform:" -ForegroundColor White
Write-Host "      cd infra/terraform/environments/production" -ForegroundColor Gray
Write-Host "      terraform init -backend-config=backend.hcl" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Crie o arquivo backend.hcl:" -ForegroundColor White
Write-Host "      bucket         = `"$BucketName`"" -ForegroundColor Gray
Write-Host "      key            = `"oraex/terraform.tfstate`"" -ForegroundColor Gray
Write-Host "      region         = `"$Region`"" -ForegroundColor Gray
Write-Host "      dynamodb_table = `"$DynamoDBTable`"" -ForegroundColor Gray
Write-Host "      encrypt        = true" -ForegroundColor Gray
