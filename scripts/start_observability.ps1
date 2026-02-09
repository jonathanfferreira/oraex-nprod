# ORAEX Observability Stack - Start Script
# -----------------------------------------
# Executa: Prometheus + Grafana + Oracle Exporter

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ORAEX Observability Stack Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Configurar Oracle Instant Client
$env:PATH = "D:\PESSOAL\ESTUDOS\Oracle\instantclient-basic-windows.x64-19.29.0.0.0dbru\instantclient_19_29;" + $env:PATH

# Configurar credenciais Oracle
$env:ORACLE_DSN = "192.168.56.12:1521/orcl"
$env:ORACLE_USER = "system"
$env:ORACLE_PASSWORD = "oracle123"

# Verificar e iniciar Prometheus
Write-Host "`n[1/3] Iniciando Prometheus..." -ForegroundColor Yellow
$prometheusProc = Get-Process -Name "prometheus" -ErrorAction SilentlyContinue
if (-not $prometheusProc) {
    Start-Process -FilePath "D:\tools\prometheus\prometheus-2.47.0.windows-amd64\prometheus.exe" `
        -ArgumentList "--config.file=D:\tools\prometheus\prometheus-2.47.0.windows-amd64\prometheus.yml" `
        -WorkingDirectory "D:\tools\prometheus\prometheus-2.47.0.windows-amd64"
    Write-Host "  Prometheus iniciado!" -ForegroundColor Green
} else {
    Write-Host "  Prometheus ja esta rodando" -ForegroundColor Gray
}

# Verificar e iniciar Grafana
Write-Host "[2/3] Iniciando Grafana..." -ForegroundColor Yellow
$grafanaProc = Get-Process -Name "grafana*" -ErrorAction SilentlyContinue
if (-not $grafanaProc) {
    Start-Process -FilePath "D:\tools\grafana\grafana-10.2.0\bin\grafana-server.exe" `
        -WorkingDirectory "D:\tools\grafana\grafana-10.2.0"
    Write-Host "  Grafana iniciado!" -ForegroundColor Green
} else {
    Write-Host "  Grafana ja esta rodando" -ForegroundColor Gray
}

# Iniciar Oracle Exporter
Write-Host "[3/3] Iniciando Oracle Exporter..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Stack Iniciada!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Prometheus:      http://localhost:9090" -ForegroundColor White
Write-Host "  Grafana:         http://localhost:3000" -ForegroundColor White
Write-Host "  Oracle Exporter: http://localhost:9161/metrics" -ForegroundColor White
Write-Host ""
Write-Host "  Login Grafana: admin / admin" -ForegroundColor Gray
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o Oracle Exporter" -ForegroundColor Yellow
Write-Host ""

# Rodar o Oracle Exporter em foreground
Set-Location "d:\antigravity\oraex\nprod"
python -m automacao.observability.oracle_exporter --port 9161
