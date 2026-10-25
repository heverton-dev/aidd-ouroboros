param(
    [string]$HarnessRoot = $HOME,
    [switch]$WhatIf,
    [switch]$DryRun,
    [switch]$Force
)

if ($WhatIf) {
    $DryRun = [switch]::Present
}

$ErrorActionPreference = "Stop"
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

$h = $HarnessRoot
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
                $marker = Join-Path $legPath ".aidd-managed"
                if (Test-Path $marker) {
                    if ($DryRun) {
                        Write-Host "[DRY] Removendo legado: $legPath"
                    } else {
                        Remove-Item -Recurse -Force $legPath
                        Write-Host "[-] Removido legado: $legPath"
                    }
                } else {
                    Write-Warning "[AVISO] Ignorando pasta legada sem marcador .aidd-managed: $legPath"
                }
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
        if ($DryRun) {
            & powershell -NoProfile -ExecutionPolicy Bypass -File $SkillSync -HarnessRoot $HarnessRoot -DryRun
        } else {
            & powershell -NoProfile -ExecutionPolicy Bypass -File $SkillSync -HarnessRoot $HarnessRoot
        }
    }
}

Write-Host "`n[OK] Todas as skills foram sincronizadas com sucesso nos harnesses."

