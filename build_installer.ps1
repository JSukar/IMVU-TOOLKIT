# Build IMVU-Emoji-Installer.exe (no Python required on end-user machines)
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

Write-Host "Building IMVU-Emoji-Installer.exe..."
python -m PyInstaller --clean imvu_emoji_installer.spec

$exe = Join-Path $PSScriptRoot "dist\IMVU-Emoji-Installer.exe"
if (Test-Path $exe) {
    Write-Host ""
    Write-Host "Success: $exe"
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  Double-click to install the emoji patch"
    Write-Host "  IMVU-Emoji-Installer.exe --restore   (undo patch)"
} else {
    Write-Error "Build failed - dist\IMVU-Emoji-Installer.exe not found."
}
