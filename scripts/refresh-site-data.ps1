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
        if ($SkipAList) { 5 } else { 7 }
    } else {
        if ($SkipAList) { 4 } else { 6 }
    }
    if ($Publish) {
        $totalSteps++
    }

    Write-Host "[$step/$totalSteps] Rebuilding homepage gallery payload..."
    python scripts/rebuild-homepage-gallery.py
    if ($LASTEXITCODE -ne 0) {
        throw "Homepage gallery rebuild failed with exit code $LASTEXITCODE."
    }
    $step++

    Write-Host "[$step/$totalSteps] Updating news digest index..."
    python scripts/update-news-digest-index.py
    if ($LASTEXITCODE -ne 0) {
        throw "News digest index update failed with exit code $LASTEXITCODE."
    }
    $step++

    Write-Host "[$step/$totalSteps] Rendering scheduled news page..."
    python scripts/render-cinematic-site.py --page news
    if ($LASTEXITCODE -ne 0) {
        throw "News page render failed with exit code $LASTEXITCODE."
    }
    $step++

    if (-not $SkipAList) {
        Write-Host "[$step/$totalSteps] Syncing A-List benchmark snapshot..."
        python scripts/sync-a-list-benchmarks.py
        if ($LASTEXITCODE -ne 0) {
            throw "A-List benchmark sync failed with exit code $LASTEXITCODE."
        }
        $step++

        Write-Host "[$step/$totalSteps] Rendering A-List pages..."
        python scripts/render-a-list.py
        if ($LASTEXITCODE -ne 0) {
            throw "A-List page render failed with exit code $LASTEXITCODE."
        }
        $step++
    }

    Write-Host "[$step/$totalSteps] Validating site..."
    $validateArgs = @('scripts/validate-site.py')
    if ($SkipAList) { $validateArgs += '--skip-alist' }
    python @validateArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Site validation failed with exit code $LASTEXITCODE."
    }
    $step++

    if ($RunSmokeTest) {
        Write-Host "[$step/$totalSteps] Running browser smoke tests..."
        powershell -ExecutionPolicy Bypass -File scripts/run-smoke-test.ps1 -Port $Port
        if ($LASTEXITCODE -ne 0) {
            throw "Browser smoke test failed with exit code $LASTEXITCODE."
        }
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
