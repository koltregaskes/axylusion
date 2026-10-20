# KOL-6327: publish guard for data/gallery.json.
# Compatible with Windows PowerShell 5.1 and PowerShell 7+.
# Fails closed: any doubt about the baseline or the current file refuses the publish.

function Invoke-GuardGit {
    # Runs git with stderr kept off the error stream (Windows PowerShell 5.1 turns
    # redirected native stderr into terminating errors when ErrorActionPreference=Stop)
    # and stdout decoded as UTF-8. Returns @{ ExitCode; Output }.
    param([string]$RepoRoot, [string[]]$GitArgs)
    $oldEap = $ErrorActionPreference
    $oldEnc = [Console]::OutputEncoding
    try {
        $ErrorActionPreference = 'Continue'
        try { [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false) } catch { }
        $out = & git -C $RepoRoot @GitArgs 2>$null
        $code = $LASTEXITCODE
    } finally {
        try { [Console]::OutputEncoding = $oldEnc } catch { }
        $ErrorActionPreference = $oldEap
    }
    [pscustomobject]@{ ExitCode = $code; Output = (@($out) -join "`n") }
}

function Get-GalleryCounts {
    # Returns item and unavailable counts, or throws if the JSON is unparseable or not
    # the expected shape: an object with an "items" array (or a top-level array) of objects.
    param([string]$JsonText, [string]$Label)
    if ([string]::IsNullOrWhiteSpace($JsonText)) { throw "Publish guard: $Label gallery.json is empty." }
    try {
        $parsed = ConvertFrom-Json -InputObject $JsonText -ErrorAction Stop
    } catch {
        throw "Publish guard: $Label gallery.json is not valid JSON: $($_.Exception.Message)"
    }
    if ($parsed -is [System.Array]) {
        $items = $parsed
    } elseif ($null -ne $parsed -and $parsed.PSObject -and ($parsed.PSObject.Properties.Name -contains 'items') -and ($parsed.items -is [System.Array])) {
        $items = $parsed.items
    } else {
        throw "Publish guard: $Label gallery.json has an unexpected shape (need an 'items' array)."
    }
    foreach ($item in $items) {
        if ($null -eq $item -or $item -is [string] -or $item -is [System.ValueType] -or $item -is [System.Array]) {
            throw "Publish guard: $Label gallery.json has a non-object entry in items."
        }
    }
    $unavailable = @($items | Where-Object { $_.media_status -eq 'unavailable' }).Count
    [pscustomobject]@{ Items = @($items).Count; Unavailable = $unavailable }
}

function Assert-GalleryNotShrunk {
    # Compares the working data/gallery.json against the verified last-published state
    # (origin/main after a fresh fetch). Throws, so the caller exits non-zero before any
    # git add/commit/push, when the baseline cannot be established, either file is
    # malformed, any count is zero, or items/unavailable flags drop by more than MaxDropPercent.
    param(
        [Parameter(Mandatory = $true)][string]$ProjectRoot,
        [double]$MaxDropPercent = 2,
        [string]$Remote = 'origin',
        [string]$Branch = 'main'
    )
    $galleryPath = Join-Path (Join-Path $ProjectRoot 'data') 'gallery.json'
    if (-not (Test-Path -LiteralPath $galleryPath)) { throw "Publish guard: data/gallery.json is missing; refusing to publish." }

    # Explicit refspec so refs/remotes/<remote>/<branch> is updated even when remote.<remote>.fetch
    # is narrowed or customised.
    $baselineRef = "refs/remotes/$Remote/$Branch"
    $refspec = "+refs/heads/${Branch}:$baselineRef"
    $fetch = Invoke-GuardGit -RepoRoot $ProjectRoot -GitArgs @('fetch', '--quiet', $Remote, $refspec)
    if ($fetch.ExitCode -ne 0) { throw "Publish guard: git fetch $Remote $refspec failed (exit $($fetch.ExitCode)); cannot verify the published baseline. Refusing to publish." }
    $sha = Invoke-GuardGit -RepoRoot $ProjectRoot -GitArgs @('rev-parse', '--verify', '--quiet', "$baselineRef^{commit}")
    if ($sha.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($sha.Output)) { throw "Publish guard: $baselineRef did not resolve after fetch; refusing to publish." }
    $baselineSha = $sha.Output.Trim()
    Write-Host "Publish guard: fetched $Remote/$Branch = $baselineSha"
    $show = Invoke-GuardGit -RepoRoot $ProjectRoot -GitArgs @('show', "${baselineRef}:data/gallery.json")
    if ($show.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($show.Output)) {
        throw "Publish guard: no published data/gallery.json at $Remote/$Branch (exit $($show.ExitCode)); refusing to publish."
    }

    $before = Get-GalleryCounts -JsonText $show.Output -Label "published ($Remote/$Branch)"
    $currentText = [System.IO.File]::ReadAllText($galleryPath, [System.Text.Encoding]::UTF8)
    $after = Get-GalleryCounts -JsonText $currentText -Label 'working copy'
    Write-Host ("Publish guard: baseline {0}/{1} @ {7}; gallery items {2} -> {3}, unavailable flags {4} -> {5} (max drop {6}%)." -f $Remote, $Branch, $before.Items, $after.Items, $before.Unavailable, $after.Unavailable, $MaxDropPercent, $baselineSha.Substring(0, 7))

    foreach ($metric in 'Items', 'Unavailable') {
        if ($before.$metric -le 0) { throw "Publish guard: published gallery $metric count is zero; refusing to publish." }
        if ($after.$metric -le 0) { throw "Publish guard: working gallery $metric count is zero; refusing to publish." }
        $old = [double]$before.$metric
        $new = [double]$after.$metric
        if ($new -lt $old) {
            $dropPercent = (($old - $new) / $old) * 100
            if ($dropPercent -gt $MaxDropPercent) {
                throw ("Publish guard: gallery {0} count dropped from {1} to {2} ({3:N1}% > {4}%). Refusing to publish. Land gallery changes on main through a PR." -f $metric, $old, $new, $dropPercent, $MaxDropPercent)
            }
        }
    }
}
