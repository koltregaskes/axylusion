# KOL-6327: tests for scripts/lib/gallery-publish-guard.ps1.
# Runs on Windows PowerShell 5.1 and PowerShell 7+. Each case builds a temp repo with a bare
# "origin", runs the guard in a child process followed by the same git add/commit/push that
# refresh-site-data.ps1 performs, and asserts the exit code plus unchanged HEAD, index and remote ref.
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$guardPath = Join-Path (Join-Path (Join-Path $repoRoot 'scripts') 'lib') 'gallery-publish-guard.ps1'
$psExe = (Get-Process -Id $PID).Path
$utf8 = New-Object System.Text.UTF8Encoding($false)
$failures = 0

function Invoke-Git {
    param([string]$Dir, [string[]]$GitArgs)
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $out = & git -C $Dir -c user.name=guard-test -c user.email=guard-test@example.invalid @GitArgs 2>&1 } finally { $ErrorActionPreference = $old }
    if ($LASTEXITCODE -ne 0) { throw "git $($GitArgs -join ' ') failed in ${Dir}: $out" }
    (@($out) -join "`n").Trim()
}

function New-GalleryJson {
    param([int]$Items = 100, [int]$Unavailable = 10)
    $list = @()
    for ($i = 0; $i -lt $Items; $i++) {
        $entry = [ordered]@{ id = "item-$i"; title = "Caf$([char]0x00E9) $i" }
        if ($i -lt $Unavailable) { $entry.media_status = 'unavailable' }
        $list += [pscustomobject]$entry
    }
    ConvertTo-Json -InputObject ([pscustomobject]@{ items = $list }) -Depth 5
}

function Write-Text { param([string]$Path, [string]$Text) [System.IO.File]::WriteAllText($Path, $Text, $utf8) }

function Invoke-Case {
    param([string]$Name, [AllowNull()][string]$Baseline, [string]$Current, [bool]$ExpectPass, [switch]$BreakRemote,
        [AllowNull()][string]$LocalCommit = $null, [AllowNull()][string]$RemoteAdvance = $null, [string]$FetchRefspec = '')
    $root = Join-Path ([System.IO.Path]::GetTempPath()) ("kol6327-" + [guid]::NewGuid().ToString('N'))
    $bare = Join-Path $root 'origin.git'; $work = Join-Path $root 'work'
    New-Item -ItemType Directory -Force -Path $root | Out-Null
    try {
        Invoke-Git -Dir $root -GitArgs @('init', '--quiet', '--bare', $bare) | Out-Null
        Invoke-Git -Dir $root -GitArgs @('init', '--quiet', $work) | Out-Null
        Invoke-Git -Dir $work -GitArgs @('checkout', '--quiet', '-b', 'main') | Out-Null
        New-Item -ItemType Directory -Force -Path (Join-Path $work 'data') | Out-Null
        Write-Text (Join-Path $work 'README.md') 'fixture'
        if ($null -ne $Baseline) { Write-Text (Join-Path (Join-Path $work 'data') 'gallery.json') $Baseline }
        Invoke-Git -Dir $work -GitArgs @('add', '-A') | Out-Null
        Invoke-Git -Dir $work -GitArgs @('commit', '--quiet', '-m', 'baseline') | Out-Null
        Invoke-Git -Dir $work -GitArgs @('remote', 'add', 'origin', $bare) | Out-Null
        Invoke-Git -Dir $work -GitArgs @('push', '--quiet', 'origin', 'main') | Out-Null
        if ($LocalCommit) {
            # Unpushed local commit: HEAD differs from origin/main.
            Write-Text (Join-Path (Join-Path $work 'data') 'gallery.json') $LocalCommit
            Invoke-Git -Dir $work -GitArgs @('commit', '--quiet', '-am', 'local-only gallery change') | Out-Null
        }
        if ($RemoteAdvance) {
            # Someone else publishes to origin/main; the local origin/main ref is now stale.
            $other = Join-Path $root 'other'
            Invoke-Git -Dir $root -GitArgs @('clone', '--quiet', '--branch', 'main', $bare, $other) | Out-Null
            Write-Text (Join-Path (Join-Path $other 'data') 'gallery.json') $RemoteAdvance
            Invoke-Git -Dir $other -GitArgs @('commit', '--quiet', '-am', 'remote gallery change') | Out-Null
            Invoke-Git -Dir $other -GitArgs @('push', '--quiet', 'origin', 'main') | Out-Null
        }
        if ($FetchRefspec) { Invoke-Git -Dir $work -GitArgs @('config', 'remote.origin.fetch', $FetchRefspec) | Out-Null }
        $script:expectedBaseline = Invoke-Git -Dir $bare -GitArgs @('rev-parse', 'refs/heads/main')
        Write-Text (Join-Path (Join-Path $work 'data') 'gallery.json') $Current
        Write-Text (Join-Path $work 'publish-marker.txt') 'would be published'
        if ($BreakRemote) { Invoke-Git -Dir $work -GitArgs @('remote', 'set-url', 'origin', (Join-Path $root 'missing.git')) | Out-Null }

        $headBefore = Invoke-Git -Dir $work -GitArgs @('rev-parse', 'HEAD')
        $remoteBefore = Invoke-Git -Dir $bare -GitArgs @('rev-parse', 'refs/heads/main')
        $indexBefore = Invoke-Git -Dir $work -GitArgs @('diff', '--cached', '--name-only')

        $child = Join-Path $root 'publish.ps1'
        $childText = @'
$ErrorActionPreference = 'Stop'
. '__GUARD__'
Assert-GalleryNotShrunk -ProjectRoot '__WORK__' -MaxDropPercent 2
Set-Location '__WORK__'
$ErrorActionPreference = 'Continue'
git -c user.name=guard-test -c user.email=guard-test@example.invalid add -A
git -c user.name=guard-test -c user.email=guard-test@example.invalid commit --quiet -m publish
git push --quiet origin main 2>&1 | Out-Null
exit $LASTEXITCODE
'@
        $childText = $childText.Replace('__GUARD__', $guardPath.Replace("'", "''")).Replace('__WORK__', $work.Replace("'", "''"))
        Write-Text $child $childText
        $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        try { $output = & $psExe -NoProfile -ExecutionPolicy Bypass -File $child 2>&1 } finally { $ErrorActionPreference = $old }
        $exit = $LASTEXITCODE
        $guardLine = @(@($output) | ForEach-Object { "$_" } | Where-Object { $_ -match 'Publish guard:' -and $_ -notmatch 'fetched origin/main' }) | Select-Object -First 1

        $headAfter = Invoke-Git -Dir $work -GitArgs @('rev-parse', 'HEAD')
        $remoteAfter = Invoke-Git -Dir $bare -GitArgs @('rev-parse', 'refs/heads/main')
        $indexAfter = Invoke-Git -Dir $work -GitArgs @('diff', '--cached', '--name-only')
        $untouched = ($headAfter -eq $headBefore) -and ($remoteAfter -eq $remoteBefore) -and ($indexAfter -eq $indexBefore)

        $fetchedLine = @(@($output) | ForEach-Object { "$_" } | Where-Object { $_ -match 'fetched origin/main = ' }) | Select-Object -First 1
        $usedBaseline = ($null -eq $fetchedLine) -or ($fetchedLine -match [regex]::Escape($script:expectedBaseline))
        if (-not $usedBaseline) { Write-Host "  baseline mismatch: expected $($script:expectedBaseline), got: $fetchedLine" }
        if ($ExpectPass) { $ok = ($exit -eq 0) -and ($remoteAfter -ne $remoteBefore) -and $usedBaseline }
        else { $ok = ($exit -ne 0) -and $untouched -and $usedBaseline }
        $status = if ($ok) { 'PASS' } else { 'FAIL' }
        if (-not $ok) { $script:failures++ }
        Write-Host ("[{0}] {1}: exit={2} head/index/remote unchanged={3} :: {4}" -f $status, $Name, $exit, $untouched, $guardLine)
        if (-not $ok) { Write-Host (@($output) -join "`n") }
    } finally {
        Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# Static check: in refresh-site-data.ps1 the guard must run before the first git add/commit/push.
$refreshText = [System.IO.File]::ReadAllText((Join-Path (Join-Path $repoRoot 'scripts') 'refresh-site-data.ps1'))
$guardAt = $refreshText.IndexOf('Assert-GalleryNotShrunk -ProjectRoot')
$addAt = $refreshText.IndexOf('git add'); $commitAt = $refreshText.IndexOf('git commit'); $pushAt = $refreshText.IndexOf('git push')
if ($guardAt -lt 0 -or $guardAt -gt $addAt -or $guardAt -gt $commitAt -or $guardAt -gt $pushAt) { Write-Host '[FAIL] refresh-site-data.ps1: guard call is missing or after git add/commit/push'; $failures++ }
else { Write-Host '[PASS] refresh-site-data.ps1 calls the guard before git add/commit/push' }

$good = New-GalleryJson -Items 100 -Unavailable 10
Write-Host "PowerShell $($PSVersionTable.PSVersion) ($($PSVersionTable.PSEdition))"
Invoke-Case -Name 'absent baseline (data/gallery.json not on origin/main)' -Baseline $null -Current $good -ExpectPass $false
Invoke-Case -Name 'empty baseline (0-byte gallery.json on origin/main)' -Baseline '' -Current $good -ExpectPass $false
Invoke-Case -Name 'fetch fails (origin unreachable)' -Baseline $good -Current $good -ExpectPass $false -BreakRemote
Invoke-Case -Name 'unparseable baseline' -Baseline '{ "items": [ ' -Current $good -ExpectPass $false
Invoke-Case -Name 'bad shape baseline (no items array)' -Baseline '{ "gallery": [ { "id": 1 } ] }' -Current $good -ExpectPass $false
Invoke-Case -Name 'bad shape current (items is an object)' -Baseline $good -Current '{ "items": { "id": 1 } }' -ExpectPass $false
Invoke-Case -Name 'zero baseline items (items: [])' -Baseline '{ "items": [] }' -Current $good -ExpectPass $false
Invoke-Case -Name 'zero current unavailable' -Baseline $good -Current (New-GalleryJson -Items 100 -Unavailable 0) -ExpectPass $false
Invoke-Case -Name 'item drop 3% (>2%)' -Baseline $good -Current (New-GalleryJson -Items 97 -Unavailable 10) -ExpectPass $false
Invoke-Case -Name 'unavailable drop 10% (>2%)' -Baseline $good -Current (New-GalleryJson -Items 100 -Unavailable 9) -ExpectPass $false
Invoke-Case -Name 'local HEAD shrunk to 97 (unpushed), current 97: rejected vs origin/main 100' -Baseline $good -LocalCommit (New-GalleryJson -Items 97 -Unavailable 10) -Current (New-GalleryJson -Items 97 -Unavailable 10) -ExpectPass $false
Invoke-Case -Name 'local HEAD grown to 120 (unpushed), current 100: passes vs origin/main 100' -Baseline $good -LocalCommit (New-GalleryJson -Items 120 -Unavailable 10) -Current $good -ExpectPass $true
Invoke-Case -Name 'stale local origin/main (remote moved to 120), current 100: rejected after fetch' -Baseline $good -RemoteAdvance (New-GalleryJson -Items 120 -Unavailable 10) -Current $good -ExpectPass $false
Invoke-Case -Name 'non-default remote.origin.fetch (refs/heads/other only), remote moved to 120: still rejected' -Baseline $good -RemoteAdvance (New-GalleryJson -Items 120 -Unavailable 10) -FetchRefspec '+refs/heads/other:refs/remotes/origin/other' -Current $good -ExpectPass $false
Invoke-Case -Name 'item drop 2% (= tolerance) passes' -Baseline $good -Current (New-GalleryJson -Items 98 -Unavailable 10) -ExpectPass $true
Invoke-Case -Name 'unchanged copy passes' -Baseline $good -Current $good -ExpectPass $true
if ($failures -gt 0) { Write-Host "$failures case(s) failed."; exit 1 }
Write-Host 'All gallery publish guard cases passed.'
exit 0
