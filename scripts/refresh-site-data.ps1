$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

Push-Location $projectRoot
try {
    Write-Host "[1/3] Updating news digest index..."
    python scripts/update-news-digest-index.py

    Write-Host "[2/3] Syncing A-List benchmark snapshot..."
    python scripts/sync-a-list-benchmarks.py

    Write-Host "[3/3] Validating site..."
    python scripts/validate-site.py
}
finally {
    Pop-Location
}
