param(
    [switch]$RunSmokeTest,
    [switch]$SkipAList,
    [int]$Port = 4173
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

Push-Location $projectRoot
try {
    $step = 1
    $totalSteps = if ($RunSmokeTest) {
        if ($SkipAList) { 4 } else { 6 }
    } else {
        if ($SkipAList) { 3 } else { 5 }
    }

    Write-Host "[$step/$totalSteps] Rebuilding homepage gallery payload..."
    python scripts/rebuild-homepage-gallery.py
    $step++

    Write-Host "[$step/$totalSteps] Updating news digest index..."
    python scripts/update-news-digest-index.py
    $step++

    if (-not $SkipAList) {
        Write-Host "[$step/$totalSteps] Syncing A-List benchmark snapshot..."
        python scripts/sync-a-list-benchmarks.py
        $step++

        Write-Host "[$step/$totalSteps] Rendering A-List pages..."
        python scripts/render-a-list.py
        $step++
    }

    Write-Host "[$step/$totalSteps] Validating site..."
    python scripts/validate-site.py
    $step++

    if ($RunSmokeTest) {
        Write-Host "[$step/$totalSteps] Running browser smoke tests..."
        powershell -ExecutionPolicy Bypass -File scripts/run-smoke-test.ps1 -Port $Port
    }
}
finally {
    Pop-Location
}
