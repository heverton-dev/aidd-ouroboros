# sync_all.ps1 - Sincronizacao Global do Almoxarifado Central para os 13 Harnesses
# Autor: Heverton Eduardo Peres (2026)

$ErrorActionPreference = "SilentlyContinue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$legacyNames = @(
    "aidd-video-reengineer",
    "aidd-web-reengineer",
    "aidd-social-reengineer",
    "aidd-app-reengineer",
    "aidd-dark-storycraft",
    "aidd-remotion-motion",
    "aidd-video-materializer",
    "aidd-tutorial-creator",
    "aidd-pipeline-creator",
    "aidd-skill-creator",
    "aidd-skill-swarm"
)

$h = $HOME
$skillDirs = @(
    "$h\.agents\skills", "$h\.claude\skills", "$h\.config\opencode\skills", "$h\.opencode\skills",
    "$h\.gemini\skills", "$h\.gemini\antigravity\skills", "$h\.gemini\antigravity-cli\skills",
    "$h\.gemini\config\skills", "$h\.cursor\skills", "$h\.hermes\skills", "$h\.cline\skills",
    "$h\.factory\skills", "$h\.mimocode\skills"
)

Write-Host "=== [AIDD-CLEANUP] Higienizando nomes legados nos 13 Harnesses ==="
foreach ($targetDir in $skillDirs) {
    if (Test-Path $targetDir) {
        foreach ($leg in $legacyNames) {
            $legPath = Join-Path $targetDir $leg
            if (Test-Path $legPath) {
                Remove-Item -Recurse -Force $legPath
                Write-Host "[-] Removido legado: $legPath"
            }
        }
    }
}

$Skills = Get-ChildItem -Path $ScriptDir -Directory | Where-Object { Test-Path "$($_.FullName)\SKILL.md" }

Write-Host "`n=== Sincronizando $($Skills.Count) skills do Almoxarifado Central ==="

foreach ($Skill in $Skills) {
    $SkillSync = Join-Path $Skill.FullName "sync.ps1"
    if (Test-Path $SkillSync) {
        Write-Host "[*] Sincronizando $($Skill.Name)..."
        & powershell -ExecutionPolicy Bypass -File $SkillSync
    }
}

Write-Host "`n[OK] Todas as skills foram sincronizadas com sucesso nos harnesses."
