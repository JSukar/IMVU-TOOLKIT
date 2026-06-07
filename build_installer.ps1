# Build IMVU-Emoji-Installer (standalone onefile GUI .exe)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Installing build dependencies (if needed)..."
python -m pip install --upgrade -r requirements-build.txt

$iconPng = Join-Path $PSScriptRoot "assets\imvu-toolkit-logo.png"
$iconIco = Join-Path $PSScriptRoot "assets\imvu-toolkit-logo.ico"
if ((Test-Path $iconPng) -and -not (Test-Path $iconIco)) {
    Write-Host "Generating icon from logo PNG..."
    python -c "from PIL import Image; img=Image.open(r'$iconPng').convert('RGBA'); img.save(r'$iconIco', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
}

Write-Host "Generating Windows version metadata..."
python scripts/generate_version_info.py

Write-Host "Building IMVU-Emoji-Installer.exe (onefile)..."
python -m PyInstaller --clean imvu_emoji_installer.spec

$exe = Join-Path $PSScriptRoot "dist\IMVU-Emoji-Installer.exe"

if (-not (Test-Path $exe)) {
    Write-Error "Build failed - $exe not found."
}

Write-Host ""
Write-Host "Success:"
Write-Host "  $exe"
Write-Host ""
Write-Host "Usage:"
Write-Host "  Run dist\IMVU-Emoji-Installer.exe"
Write-Host "  If Defender blocks the .exe, use:  .\install.ps1  or  .\install_gui.ps1"
Write-Host "  Restore (GUI): IMVU-Emoji-Installer.exe --restore"
Write-Host "  Restore (CLI): IMVU-Emoji-Installer.exe --cli --restore"
