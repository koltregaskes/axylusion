param(
    [string]$BaseUrl,
    [int]$Port = 4173,
    [Alias("ChromeExecutable")]
    [string]$BrowserExecutable = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    [string]$ScreenshotDirectory
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path -LiteralPath $BrowserExecutable)) {
    $alternateEdgePath = "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    if (Test-Path -LiteralPath $alternateEdgePath) {
        $BrowserExecutable = $alternateEdgePath
    }
    else {
        throw "Microsoft Edge was not found at either standard installation path."
    }
}

function Test-PortAvailable {
    param([int]$CandidatePort)

    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $CandidatePort)
        $listener.Start()
        $listener.Stop()
        return $true
    }
    catch {
        return $false
    }
}

function Get-AvailablePort {
    param([int]$StartPort)

    for ($candidate = $StartPort; $candidate -lt ($StartPort + 20); $candidate++) {
        if (Test-PortAvailable -CandidatePort $candidate) {
            return $candidate
        }
    }

    throw "Unable to find a free local preview port."
}

function Get-PlaywrightNodePath {
    $cacheRoot = Join-Path $env:LOCALAPPDATA "npm-cache\_npx"
    if (-not (Test-Path $cacheRoot)) {
        cmd /c npx playwright --version | Out-Null
    }

    $candidates = Get-ChildItem $cacheRoot -Directory -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending

    foreach ($candidate in $candidates) {
        $nodeModules = Join-Path $candidate.FullName "node_modules"
        if (Test-Path (Join-Path $nodeModules "playwright")) {
            return $nodeModules
        }
    }

    cmd /c npx playwright --version | Out-Null
    $candidates = Get-ChildItem $cacheRoot -Directory -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending

    foreach ($candidate in $candidates) {
        $nodeModules = Join-Path $candidate.FullName "node_modules"
        if (Test-Path (Join-Path $nodeModules "playwright")) {
            return $nodeModules
        }
    }

    throw "Unable to locate a Playwright package in the npm cache."
}

$nodePath = Get-PlaywrightNodePath
if (-not $BaseUrl) {
    $Port = Get-AvailablePort -StartPort $Port
    $BaseUrl = "http://127.0.0.1:$Port"
}

$serverProcess = Start-Process -FilePath python -ArgumentList "-m", "http.server", "--bind", "127.0.0.1", $Port -WorkingDirectory $projectRoot -PassThru -WindowStyle Hidden

try {
    $serverReady = $false
    for ($attempt = 0; $attempt -lt 10; $attempt++) {
        Start-Sleep -Milliseconds 500
        try {
            $response = Invoke-WebRequest -Uri "$BaseUrl/index.html" -TimeoutSec 2 -UseBasicParsing
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                $serverReady = $true
                break
            }
        }
        catch {
            Start-Sleep -Milliseconds 250
        }
    }

    if (-not $serverReady) {
        throw "Preview server did not become ready at $BaseUrl"
    }

    $env:NODE_PATH = $nodePath
    $env:PLAYWRIGHT_MODULE_PATH = $nodePath
    $smokeArgs = @(
        "scripts/smoke-test-site.mjs",
        "--base-url", $BaseUrl,
        "--browser-executable", $BrowserExecutable
    )
    if ($ScreenshotDirectory) {
        $smokeArgs += @("--screenshot-dir", $ScreenshotDirectory)
    }
    node @smokeArgs
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
finally {
    if ($serverProcess -and -not $serverProcess.HasExited) {
        Stop-Process -Id $serverProcess.Id -Force
    }
}
