# Build IMVU-Emoji-Installer (onedir folder + zip for releases)
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

Write-Host "Building IMVU-Emoji-Installer (onedir)..."
python -m PyInstaller --clean imvu_emoji_installer.spec

$dir = Join-Path $PSScriptRoot "dist\IMVU-Emoji-Installer"
$exe = Join-Path $dir "IMVU-Emoji-Installer.exe"
$zip = Join-Path $PSScriptRoot "dist\IMVU-Emoji-Installer.zip"

if (-not (Test-Path $exe)) {
    Write-Error "Build failed - $exe not found."
}

if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path $dir -DestinationPath $zip -Force

Write-Host ""
Write-Host "Success:"
Write-Host "  Folder: $dir"
Write-Host "  Zip:    $zip"
Write-Host ""
Write-Host "Usage:"
Write-Host "  Run dist\IMVU-Emoji-Installer\IMVU-Emoji-Installer.exe"
Write-Host "  Or extract IMVU-Emoji-Installer.zip and run the .exe inside"
Write-Host "  If Defender blocks the .exe, use:  .\install.ps1"
Write-Host "  Restore: IMVU-Emoji-Installer.exe --restore"
