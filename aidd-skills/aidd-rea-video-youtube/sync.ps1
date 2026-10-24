# Instala a skill aidd-rea-video-youtube em NIVEL GLOBAL nas harnesses da maquina.
# Fonte: a pasta deste script. Uso: powershell -File sync.ps1 [-DryRun]
param([switch]$DryRun)
$name = 'aidd-rea-video-youtube'
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
  if (-not (Test-Path $t) -and -not $alwaysCreate) { Write-Output "SKIP  $t (harness ausente)"; continue }
  $dest = Join-Path $t $name
  if ((Test-Path $dest) -and ((Resolve-Path $dest).Path -eq (Resolve-Path $src).Path)) { Write-Output "SKIP  $dest (mesma fonte)"; continue }
  if ($DryRun) { Write-Output "DRY   $dest"; continue }
  New-Item -ItemType Directory -Force $dest | Out-Null
  Copy-Item -Recurse -Force "$src\*" $dest -Exclude '__pycache__','graphify-out','.graphifyignore'
  Write-Output "OK    $dest"
}
$cmds = @(
  @("$h\.claude\commands", "$name.md"),
  @("$h\.gemini\antigravity\commands", "$name.md"),
  @("$h\.gemini\commands", "$name.toml")
)
foreach ($c in $cmds) {
  if (-not (Test-Path $c[0])) { Write-Output "SKIP  $($c[0]) (ausente)"; continue }
  if ($DryRun) { Write-Output "DRY   $($c[0])\$($c[1])"; continue }
  $srcCmd = Join-Path $src "commands\$($c[1])"
  if (Test-Path $srcCmd) {
    Copy-Item -Force $srcCmd (Join-Path $c[0] $c[1])
    Write-Output "OK    $($c[0])\$($c[1])"
  }
}
