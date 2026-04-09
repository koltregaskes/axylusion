$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

Push-Location $projectRoot
try {
    Write-Host "[1/4] Rebuilding homepage gallery payload..."
    python scripts/rebuild-homepage-gallery.py

    Write-Host "[2/4] Updating news digest index..."
    python scripts/update-news-digest-index.py

    Write-Host "[3/4] Syncing A-List benchmark snapshot..."
    python scripts/sync-a-list-benchmarks.py

    Write-Host "[4/4] Validating site..."
    python scripts/validate-site.py
}
finally {
    Pop-Location
}
