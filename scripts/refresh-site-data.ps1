param(
    [switch]$RunSmokeTest,
    [switch]$SkipAList,
    [switch]$Publish,
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
    if ($Publish) {
        $totalSteps++
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
        $step++
    }

    if ($Publish) {
        Write-Host "[$step/$totalSteps] Publishing generated output..."
        $candidatePaths = @(
            "data",
            "news-digests",
            "a-list",
            "a-list.html",
            "news.html",
            "index.html",
            "gallery.html",
            "gallery.js",
            "sitemap.xml"
        )
        $publishPaths = @($candidatePaths | Where-Object { Test-Path (Join-Path $projectRoot $_) })
        if ($publishPaths.Count -eq 0) {
            Write-Host "No publishable output paths found."
            return
        }

        $changes = @(git status --porcelain -- $publishPaths)
        if ($LASTEXITCODE -ne 0) {
            throw "git status failed with exit code $LASTEXITCODE."
        }

        if ($changes.Count -eq 0) {
            Write-Host "No generated output changes detected."
            return
        }

        git add -- $publishPaths
        if ($LASTEXITCODE -ne 0) {
            throw "git add failed with exit code $LASTEXITCODE."
        }

        $staged = @(git diff --cached --name-only)
        if ($LASTEXITCODE -ne 0) {
            throw "git diff failed with exit code $LASTEXITCODE."
        }

        if ($staged.Count -eq 0) {
            Write-Host "No staged generated output changes remain."
            return
        }

        $commitDate = Get-Date -Format "yyyy-MM-dd"
        git commit -m "chore: publish Axy Lusion refresh $commitDate [automated]"
        if ($LASTEXITCODE -ne 0) {
            throw "git commit failed with exit code $LASTEXITCODE."
        }

        git push origin main
        if ($LASTEXITCODE -ne 0) {
            throw "git push failed with exit code $LASTEXITCODE. The commit remains local."
        }

        $publishedCommit = git rev-parse --short HEAD
        Write-Host "Published generated output in commit $publishedCommit."
    }
}
finally {
    Pop-Location
}
