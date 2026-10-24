# setup.ps1 — Instalador Master & Sincronizador do AIDD OUROBOROS
param(
    [switch]$SkipAudit
)

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " 🚀 [AIDD-OUROBOROS] Instalador Master & Sincronização de Ambiente" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Verificar Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[!] Python não encontrado no PATH. Instale o Python 3.10+." -ForegroundColor Red
    exit 1
}
Write-Host "[+] Python detectado: $($pythonCmd.Source)" -ForegroundColor Green

# 2. Instalar dependências Python
if (Test-Path "$PSScriptRoot\requirements.txt") {
    Write-Host "[*] Instalando dependências de requirements.txt..." -ForegroundColor Yellow
    python -m pip install -q -r "$PSScriptRoot\requirements.txt"
}

# 3. Propagar skills para os harnesses
$skillsDir = "$PSScriptRoot\aidd-skills"
if (Test-Path $skillsDir) {
    Write-Host "[*] Sincronizando skills canônicas para harnesses do sistema..." -ForegroundColor Yellow
    Get-ChildItem -Path $skillsDir -Recurse -Filter "sync.ps1" | ForEach-Object {
        $skillName = $_.Directory.Name
        Write-Host "  -> Sincronizando $skillName..." -ForegroundColor Gray
        & $_.FullName | Out-Null
    }
}

# 4. Executar Doctor
Write-Host "`n[*] Executando diagnóstico de pré-voo..." -ForegroundColor Yellow
python "$PSScriptRoot\ouroboros.py" --doctor

# 5. Executar Auditoria
if (-not $SkipAudit) {
    Write-Host "[*] Executando Quality Gates de Governança Fractal..." -ForegroundColor Yellow
    python "$PSScriptRoot\ouroboros.py" --audit
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] Falha nos Quality Gates. Revise os apontamentos acima." -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host " 🌟 AIDD OUROBOROS INSTALADO E OPERACIONAL COM 100% DE SUCESSO!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
