# Install or restore the IMVU room antibot patch without the PyInstaller .exe.
#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$restore = $args -contains "--restore"
Push-Location $PSScriptRoot
try {
    Write-Host "IMVU Antibot Patch (Python) — https://github.com/JSukar/IMVU-TOOLKIT"
    Write-Host ""
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Error "Python not found. Install Python 3.10+ from https://python.org and try again."
    }
    python -m pip install -e . -q
    if ($restore) {
        python -m imvu_toolkit antibot restore --relaunch-imvu
    } else {
        python -m imvu_toolkit antibot install --relaunch-imvu
    }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host ""
    if ($restore) {
        Write-Host "Restore complete."
    } else {
        Write-Host "Install complete. Use the shield icon beside Send in chat."
    }
} finally {
    Pop-Location
}
if ($Host.Name -eq "ConsoleHost") {
    Read-Host "Press Enter to exit"
}
