# Sincronização multi-harness para aidd-craft-story-ptbr
param([switch]$DryRun)
$name = 'aidd-craft-story-ptbr'
$src = $PSScriptRoot
$h = $HOME
$skillDirs = @(
  "$h\.agents\skills", "$h\.claude\skills", "$h\.config\opencode\skills", "$h\.opencode\skills",
  "$h\.gemini\skills", "$h\.gemini\antigravity\skills", "$h\.gemini\antigravity-cli\skills",
  "$h\.gemini\config\skills", "$h\.cursor\skills", "$h\.hermes\skills", "$h\.cline\skills",
  "$h\.factory\skills", "$h\.mimocode\skills"
)
foreach ($t in $skillDirs) {
  $alwaysCreate = $t -like '*\.agents\skills' -or $t -like '*\.gemini\config\skills'
  if (-not (Test-Path $t) -and -not $alwaysCreate) { continue }
  $dest = Join-Path $t $name
  if ((Test-Path $dest) -and ((Resolve-Path $dest).Path -eq (Resolve-Path $src).Path)) { continue }
  if ($DryRun) { Write-Output "DRY $dest"; continue }
  New-Item -ItemType Directory -Force $dest | Out-Null
  Copy-Item -Recurse -Force "$src\*" $dest -Exclude '__pycache__'
  Write-Output "OK  $dest"
}
