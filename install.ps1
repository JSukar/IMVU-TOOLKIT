# Install or restore the IMVU emoji patch without the PyInstaller .exe (avoids Defender false positives).
#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$restore = $args -contains "--restore"
Push-Location $PSScriptRoot
try {
    Write-Host "IMVU Emoji Patch (Python) — https://github.com/JSukar/IMVU-TOOLKIT"
    Write-Host ""
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Error "Python not found. Install Python 3.10+ from https://python.org and try again."
    }
    python -m pip install -e . -q
    if ($restore) {
        python -m imvu_toolkit emoji restore
    } else {
        Write-Host "Close IMVU before continuing."
        python -m imvu_toolkit emoji install --no-close-imvu
    }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host ""
    if ($restore) {
        Write-Host "Restore complete. Restart IMVU."
    } else {
        Write-Host "Install complete. Restart IMVU and click the smiley button beside Send."
    }
} finally {
    Pop-Location
}
if ($Host.Name -eq "ConsoleHost") {
    Read-Host "Press Enter to exit"
}
