param(
  [string[]]$Target,
  [switch]$Force
)

$ErrorActionPreference = "Stop"

if (-not $Target -or $Target.Count -eq 0) {
  $Target = @(
    (Join-Path $HOME ".codex\skills"),
    (Join-Path $HOME ".claude\skills")
  )
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsRoot = Join-Path $Root "skills"

foreach ($TargetDir in $Target) {
  New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
  Get-ChildItem -Path $SkillsRoot -Directory -Filter "ebiaobiao-*" | ForEach-Object {
    $Destination = Join-Path $TargetDir $_.Name
    if ((Test-Path $Destination) -and (-not $Force)) {
      Write-Host "skip existing: $Destination"
    } else {
      if (Test-Path $Destination) {
        Remove-Item -Recurse -Force $Destination
      }
      Copy-Item -Recurse -Force $_.FullName $Destination
      Get-ChildItem -Path $Destination -Recurse -Force |
        Where-Object {
          ($_.PSIsContainer -and @("node_modules", "dist", "__pycache__") -contains $_.Name) -or
          (-not $_.PSIsContainer -and ($_.Name -eq "package-lock.json" -or $_.Name -like "*.pyc"))
        } |
        Sort-Object FullName -Descending |
        Remove-Item -Recurse -Force
      Write-Host "installed: $Destination"
    }
  }
}

Write-Host "done"
