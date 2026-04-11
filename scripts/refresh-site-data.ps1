param(
    [switch]$RunSmokeTest,
    [int]$Port = 4173
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

Push-Location $projectRoot
try {
    Write-Host "[1/5] Rebuilding homepage gallery payload..."
    python scripts/rebuild-homepage-gallery.py

    Write-Host "[2/5] Updating news digest index..."
    python scripts/update-news-digest-index.py

    Write-Host "[3/5] Syncing A-List benchmark snapshot..."
    python scripts/sync-a-list-benchmarks.py

    Write-Host "[4/5] Rendering A-List pages..."
    python scripts/render-a-list.py

    Write-Host "[5/5] Validating site..."
    python scripts/validate-site.py

    if ($RunSmokeTest) {
        Write-Host "[6/6] Running browser smoke tests..."
        powershell -ExecutionPolicy Bypass -File scripts/run-smoke-test.ps1 -Port $Port
    }
}
finally {
    Pop-Location
}
