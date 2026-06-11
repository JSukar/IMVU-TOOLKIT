# Build IMVU patch installers (standalone onefile GUI .exe)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Installing build dependencies (if needed)..."
python -m pip install --upgrade -r requirements-build.txt

$iconPng = Join-Path $PSScriptRoot "assets\imvu-toolkit-logo.png"
$iconIco = Join-Path $PSScriptRoot "assets\imvu-toolkit-logo.ico"
if (Test-Path $iconPng) {
    Write-Host "Generating transparent icon from logo PNG..."
    python scripts/generate_icon.py
}

Write-Host "Generating Windows version metadata..."
python scripts/generate_version_info.py

Write-Host "Building IMVU-Emoji-Installer.exe (onefile)..."
python -m PyInstaller --clean imvu_emoji_installer.spec

Write-Host "Building IMVU-Antibot-Installer.exe (onefile)..."
python -m PyInstaller --clean imvu_antibot_installer.spec

$emojiExe = Join-Path $PSScriptRoot "dist\IMVU-Emoji-Installer.exe"
$antibotExe = Join-Path $PSScriptRoot "dist\IMVU-Antibot-Installer.exe"

if (-not (Test-Path $emojiExe)) {
    Write-Error "Build failed - $emojiExe not found."
}
if (-not (Test-Path $antibotExe)) {
    Write-Error "Build failed - $antibotExe not found."
}

Write-Host ""
Write-Host "Success:"
Write-Host "  $emojiExe"
Write-Host "  $antibotExe"
Write-Host ""
Write-Host "Emoji usage:"
Write-Host "  Run dist\IMVU-Emoji-Installer.exe"
Write-Host "  If Defender blocks the .exe, use:  .\install.ps1  or  .\install_gui.ps1"
Write-Host "  Restore (GUI): IMVU-Emoji-Installer.exe --restore"
Write-Host "  Restore (CLI): IMVU-Emoji-Installer.exe --cli --restore"
Write-Host ""
Write-Host "Antibot usage:"
Write-Host "  Run dist\IMVU-Antibot-Installer.exe"
Write-Host "  If Defender blocks the .exe, use:  .\install_antibot.ps1  or  .\install_antibot_gui.ps1"
Write-Host "  Restore (GUI): IMVU-Antibot-Installer.exe --restore"
Write-Host "  Restore (CLI): IMVU-Antibot-Installer.exe --cli --restore"
