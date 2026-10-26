# setup.ps1 — Instalador Master & Sincronizador do AIDD OUROBOROS
param(
    [switch]$SkipAudit,
    [switch]$ForcePip
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " 🚀 [AIDD-OUROBOROS] Instalador Master (UV preferencial)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Detectar runtime
$uv = Get-Command uv -ErrorAction SilentlyContinue
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[!] Python não encontrado no PATH. Instale o Python 3.10+." -ForegroundColor Red
    exit 1
}
Write-Host "[+] Python: $($pythonCmd.Source)" -ForegroundColor Green

# 2. Instalar pacote editável (console script `ouroboros`)
$installed = $false
if ($uv -and -not $ForcePip) {
    Write-Host "[*] Instalando aidd-ouroboros via uv..." -ForegroundColor Yellow
    Push-Location $Root
    try {
        # Preferir venv local; se não existir, system (admin/CI)
        if (-not (Test-Path (Join-Path $Root ".venv"))) {
            uv venv $Root --quiet
        }
        if (Test-Path (Join-Path $Root ".venv")) {
            $env:VIRTUAL_ENV = Join-Path $Root ".venv"
            $env:PATH = (Join-Path $Root ".venv\Scripts") + [IO.Path]::PathSeparator + $env:PATH
            uv pip install -e $Root
        } else {
            uv pip install --system -e $Root
        }
        if ($LASTEXITCODE -eq 0) { $installed = $true }
        else { Write-Host "[!] uv falhou; fallback para pip..." -ForegroundColor Yellow }
    } finally {
        Pop-Location
    }
}
if (-not $installed) {
    Write-Host "[*] Instalando aidd-ouroboros via pip (editável)..." -ForegroundColor Yellow
    & $pythonCmd.Source -m pip install -e $Root
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] Falha ao instalar o pacote." -ForegroundColor Red
        exit 1
    }
}

# 3. Sincronizar skills multi-harness (mestra primeiro)
$skillsDir = Join-Path $Root "aidd-skills"
if (Test-Path $skillsDir) {
    Write-Host "[*] Sincronizando skills (aidd-ouroboros-master primeiro)..." -ForegroundColor Yellow
    $masterSync = Join-Path $skillsDir "aidd-ouroboros-master\sync.ps1"
    if (Test-Path $masterSync) {
        Write-Host "  -> aidd-ouroboros-master" -ForegroundColor Gray
        & $masterSync | Out-Null
    }
    Get-ChildItem -Path $skillsDir -Filter "sync.ps1" -Recurse | Where-Object {
        $_.Directory.Name -ne "aidd-ouroboros-master"
    } | ForEach-Object {
        Write-Host "  -> $($_.Directory.Name)" -ForegroundColor Gray
        & $_.FullName | Out-Null
    }
}

# 4. Exportar root para console script fora do repo
$env:AIDD_OUROBOROS_ROOT = $Root
[Environment]::SetEnvironmentVariable("AIDD_OUROBOROS_ROOT", $Root, "User")

# 5. Doctor + Master Doctor + Audit
Write-Host "`n[*] Diagnóstico do ecossistema..." -ForegroundColor Yellow
& $pythonCmd.Source (Join-Path $Root "ouroboros.py") --doctor
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Doctor falhou." -ForegroundColor Red
    exit 1
}

Write-Host "[*] Diagnóstico da skill mestra..." -ForegroundColor Yellow
& $pythonCmd.Source (Join-Path $Root "ouroboros.py") --master-doctor
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Master doctor falhou." -ForegroundColor Red
    exit 1
}

if (-not $SkipAudit) {
    Write-Host "[*] Quality Gates..." -ForegroundColor Yellow
    & $pythonCmd.Source (Join-Path $Root "ouroboros.py") --audit
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] Falha nos Quality Gates." -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host " 🌟 AIDD OUROBOROS INSTALADO E OPERACIONAL" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " Comandos:" -ForegroundColor Cyan
Write-Host "   ouroboros --doctor"
Write-Host "   ouroboros --from-nl `"criar pipeline X a partir de https://y`""
Write-Host "   ouroboros --orchestrate .\SPEC_PIPELINE.json"
Write-Host "   /ouroboros   (no harness de agentes)"
Write-Host ""
