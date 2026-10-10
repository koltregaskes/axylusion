param(
    [string]$BaseUrl,
    [int]$Port = 4173,
    [ValidateRange(5, 120)]
    [int]$PreviewReadyTimeoutSeconds = 30,
    [string]$ChromeExecutable = "C:\Program Files\Google\Chrome\Application\chrome.exe"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$smokeTestScript = Join-Path $PSScriptRoot 'smoke-test-site.mjs'

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
        cmd /c npx --yes playwright --version | Out-Null
    }

    $candidates = Get-ChildItem $cacheRoot -Directory -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending

    foreach ($candidate in $candidates) {
        $nodeModules = Join-Path $candidate.FullName "node_modules"
        if (Test-Path (Join-Path $nodeModules "playwright")) {
            return $nodeModules
        }
    }

    cmd /c npx --yes playwright --version | Out-Null
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

$pythonExecutable = (Get-Command python -ErrorAction Stop).Source
$serverStdout = [System.IO.Path]::GetTempFileName()
$serverStderr = [System.IO.Path]::GetTempFileName()
$serverProcess = $null

try {
    $serverProcess = Start-Process -FilePath $pythonExecutable `
        -ArgumentList "-m", "http.server", "--bind", "127.0.0.1", $Port `
        -WorkingDirectory $projectRoot -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput $serverStdout -RedirectStandardError $serverStderr

    $serverReady = $false
    $serverWait = [System.Diagnostics.Stopwatch]::StartNew()
    while ($serverWait.Elapsed.TotalSeconds -lt $PreviewReadyTimeoutSeconds) {
        if ($serverProcess.HasExited) {
            break
        }

        try {
            $response = Invoke-WebRequest -Uri "$BaseUrl/index.html" -TimeoutSec 2 -UseBasicParsing
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                $serverReady = $true
                break
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }

    if (-not $serverReady) {
        $processWasRunning = -not $serverProcess.HasExited
        $exitDetail = if (-not $processWasRunning) {
            "exited with code $($serverProcess.ExitCode)"
        } else {
            'was still running'
        }
        if ($processWasRunning) {
            Stop-Process -Id $serverProcess.Id -Force
            $serverProcess.WaitForExit()
        }
        $stderrDetail = [System.IO.File]::ReadAllText($serverStderr).Trim()
        if ($stderrDetail.Length -gt 1000) {
            $stderrDetail = $stderrDetail.Substring($stderrDetail.Length - 1000)
        }
        if (-not $stderrDetail) {
            $stderrDetail = '<empty>'
        }

        throw "Preview server did not become ready at $BaseUrl within $PreviewReadyTimeoutSeconds seconds; process $exitDetail; stderr: $stderrDetail"
    }

    Write-Host "Preview server ready at $BaseUrl after $([int]$serverWait.Elapsed.TotalMilliseconds)ms."

    $env:NODE_PATH = $nodePath
    $env:PLAYWRIGHT_MODULE_PATH = $nodePath
    & node $smokeTestScript --base-url $BaseUrl --chrome-executable $ChromeExecutable
    if ($LASTEXITCODE -ne 0) {
        throw "Browser smoke test failed with exit code $LASTEXITCODE."
    }
}
finally {
    if ($serverProcess -and -not $serverProcess.HasExited) {
        Stop-Process -Id $serverProcess.Id -Force
        $serverProcess.WaitForExit()
    }
    Remove-Item -LiteralPath $serverStdout, $serverStderr -Force -ErrorAction SilentlyContinue
}
