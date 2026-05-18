# Script de Compilação Automática do ERP Guardian Agent
# ERP Guardian AI Factory

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "🔨 COMPILANDO ERP GUARDIAN AGENT EM UM EXECUTA VEL ÚNICO" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

# 1. Garantir que o PyInstaller está instalado
Write-Host "📦 Verificando/Instalando PyInstaller..." -ForegroundColor Cyan
pip install pyinstaller --upgrade

# 2. Limpar builds anteriores
Write-Host "🧹 Limpando compilações antigas..." -ForegroundColor Cyan
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist

# 3. Executar o PyInstaller
# Incluímos todas as subpastas e dependências internas necessárias para o Agente funcionar sem o código Python original
Write-Host "🚀 Compilando o Agente (Isso pode levar de 1 a 2 minutos)..." -ForegroundColor Cyan
pyinstaller --noconfirm --onedir --console --name "ERPGuardianAgent" `
    --paths="." `
    --add-data "shared;shared" `
    --add-data "orchestrator;orchestrator" `
    --add-data "workflow_engine;workflow_engine" `
    --add-data "agents;agents" `
    --add-data "agent/samples;agent/samples" `
    --hidden-import "pywinauto" `
    --hidden-import "watchdog" `
    --hidden-import "requests" `
    --hidden-import "sqlalchemy" `
    --hidden-import "psycopg2" `
    --hidden-import "google.generativeai" `
    agent/runtime.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Agente Compilado com sucesso na pasta 'dist/ERPGuardianAgent'!" -ForegroundColor Green
    Write-Host "--------------------------------------------------------" -ForegroundColor Green
    Write-Host "Para gerar o instalador final sem Admin:" -ForegroundColor Yellow
    Write-Host "1. Abra o Inno Setup." -ForegroundColor Yellow
    Write-Host "2. Carregue o arquivo 'setup.iss'." -ForegroundColor Yellow
    Write-Host "3. Pressione F9 (ou clique em Build > Compile)." -ForegroundColor Yellow
    Write-Host "O instalador estará pronto em 'dist/ERPGuardianAgent_Setup.exe'!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Erro durante a compilação do PyInstaller." -ForegroundColor Red
}
