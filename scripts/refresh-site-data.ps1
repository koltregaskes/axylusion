param(
    [switch]$RunSmokeTest,
    [switch]$SkipAList,
    [switch]$Publish,
    [int]$Port = 4173,
    # KOL-6327: refuse to publish if gallery.json loses items or unavailable flags.
    [ValidateRange(0, 50)]
    [double]$MaxGalleryDropPercent = 2
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

function Get-GalleryCounts {
    param([string]$JsonText)
    $parsed = $JsonText | ConvertFrom-Json
    $items = if ($parsed -is [System.Array]) { $parsed } elseif ($parsed.PSObject.Properties.Name -contains 'items') { @($parsed.items) } else { @() }
    $unavailable = @($items | Where-Object { $_.media_status -eq 'unavailable' }).Count
    [pscustomobject]@{ Items = @($items).Count; Unavailable = $unavailable }
}

function Assert-GalleryNotShrunk {
    # KOL-6327: the 18 Oct 2026 refresh published a gallery.json that had lost 109
    # media_status flags. Compare the working copy with the last published commit and
    # stop (non-zero exit, no commit, no push) if items or unavailable flags drop.
    param([double]$MaxDropPercent)
    $galleryPath = Join-Path $projectRoot 'data\gallery.json'
    if (-not (Test-Path $galleryPath)) { throw "Publish guard: data/gallery.json is missing; refusing to publish." }
    $publishedText = (git show HEAD:data/gallery.json 2>$null) -join "`n"
    if ($LASTEXITCODE -ne 0 -or -not $publishedText) {
        Write-Host "Publish guard: no published data/gallery.json at HEAD to compare against; skipping count check."
        return
    }
    $before = Get-GalleryCounts -JsonText $publishedText
    $after = Get-GalleryCounts -JsonText (Get-Content -Raw -Encoding UTF8 $galleryPath)
    Write-Host ("Publish guard: gallery items {0} -> {1}, unavailable flags {2} -> {3} (max drop {4}%)." -f $before.Items, $after.Items, $before.Unavailable, $after.Unavailable, $MaxDropPercent)
    foreach ($metric in 'Items', 'Unavailable') {
        $old = [double]$before.$metric
        $new = [double]$after.$metric
        if ($old -gt 0 -and $new -lt $old) {
            $dropPercent = (($old - $new) / $old) * 100
            if ($dropPercent -gt $MaxDropPercent) {
                throw ("Publish guard: gallery {0} count dropped from {1} to {2} ({3:N1}% > {4}%). Refusing to publish. Land gallery changes on main through a PR." -f $metric, $old, $new, $dropPercent, $MaxDropPercent)
            }
        }
    }
}

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
        Assert-GalleryNotShrunk -MaxDropPercent $MaxGalleryDropPercent
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

        # Never publish a routed digest that reports 0 stories: unstage it, log it, carry on.
        $stagedDigests = @(git diff --cached --name-only -- "news-digests/*.md")
        foreach ($digestPath in $stagedDigests) {
            $digestFile = Join-Path $projectRoot $digestPath
            if ((Test-Path $digestFile) -and (Select-String -Path $digestFile -Pattern '^\*\*\d{4}-\d{2}-\d{2}\*\*\s*\|\s*0\s+stories\b' -Quiet)) {
                Write-Host "Skipping publish of empty digest (0 stories): $digestPath"
                git reset -q -- $digestPath
                if ($LASTEXITCODE -ne 0) {
                    throw "git reset failed for $digestPath with exit code $LASTEXITCODE."
                }
            }
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
