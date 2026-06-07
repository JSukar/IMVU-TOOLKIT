# Launch the GUI emoji patch installer (requires Python 3.10+).
#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$restore = $args -contains "--restore"
Push-Location $PSScriptRoot
try {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Error "Python not found. Install Python 3.10+ from https://python.org and try again."
    }
    python -m pip install -e ".[gui]" -q
    if ($restore) {
        python imvu_emoji_installer.py --restore
    } else {
        python imvu_emoji_installer.py
    }
} finally {
    Pop-Location
}
