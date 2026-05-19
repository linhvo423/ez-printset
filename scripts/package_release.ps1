$ErrorActionPreference = "Stop"

$releaseDir = "release"
$zipPath = Join-Path $releaseDir "EZ-PrintSet-windows.zip"

if (!(Test-Path "dist\EZ-PrintSet.exe")) {
  powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
}

New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
if (Test-Path $zipPath) {
  Remove-Item $zipPath
}

Compress-Archive -Path "dist\EZ-PrintSet.exe", "README.md" -DestinationPath $zipPath
Write-Host "Package complete: $zipPath"
