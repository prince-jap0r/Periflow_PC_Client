$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$payloadDist = Join-Path $projectRoot "payload_dist"
$payloadBuild = Join-Path $projectRoot "build_payload"
$installerDist = Join-Path $projectRoot "installer_dist"
$installerBuild = Join-Path $projectRoot "build_installer"
$releaseDist = Join-Path $projectRoot "dist"
$finalInstaller = Join-Path $releaseDist "periflow.exe"
$iconPath = Join-Path $projectRoot "build_assets\periflow.ico"

if (-not (Test-Path $venvPython)) {
  Write-Host "Creating local virtual environment in .venv..."
  python -m venv .venv
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPython)) {
    throw "Could not create .venv. Make sure Python 3.9+ is installed and available as 'python'."
  }
}

$pythonExe = $venvPython

Write-Host "Installing dependencies into .venv..."
& $pythonExe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
  throw "Failed to install requirements into .venv."
}

Write-Host "Preparing icon and bundled logo assets..."
& $pythonExe tools\prepare_assets.py
if ($LASTEXITCODE -ne 0) {
  throw "Failed to prepare build assets."
}

if (Test-Path $payloadDist) {
  Remove-Item -LiteralPath $payloadDist -Recurse -Force
}
if (Test-Path $payloadBuild) {
  Remove-Item -LiteralPath $payloadBuild -Recurse -Force
}
if (Test-Path $installerDist) {
  Remove-Item -LiteralPath $installerDist -Recurse -Force
}
if (Test-Path $installerBuild) {
  Remove-Item -LiteralPath $installerBuild -Recurse -Force
}
if (Test-Path $releaseDist) {
  Remove-Item -LiteralPath $releaseDist -Recurse -Force
}

New-Item -ItemType Directory -Path $payloadDist | Out-Null
New-Item -ItemType Directory -Path $releaseDist | Out-Null

Write-Host "Building Periflow application..."
& $pythonExe -m PyInstaller `
  --noconfirm `
  --clean `
  --distpath $payloadDist `
  --workpath $payloadBuild `
  Periflow_PC.spec

if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller build failed."
}

Write-Host "Building single-file installer periflow.exe..."
& $pythonExe -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name periflow `
  --specpath $installerBuild `
  --icon $iconPath `
  --add-data "$payloadDist\Periflow_PC.exe;payload" `
  installer_main.py `
  --distpath $installerDist `
  --workpath $installerBuild

if ($LASTEXITCODE -ne 0) {
  throw "Installer build failed."
}

Copy-Item -LiteralPath (Join-Path $installerDist "periflow.exe") -Destination $finalInstaller -Force

Write-Host "Build complete."
Write-Host "Single-file installer: dist\periflow.exe"
