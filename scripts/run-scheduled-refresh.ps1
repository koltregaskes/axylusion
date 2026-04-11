param(
    [ValidateSet("Morning", "Evening")]
    [string]$Mode = "Morning"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$runLogged = "W:\Websites\schedules\monitoring\Run-Logged.ps1"
$refreshScript = Join-Path $PSScriptRoot "refresh-site-data.ps1"

$taskName = switch ($Mode) {
    "Morning" { "Websites-AxyLusion-Refresh-Morning" }
    "Evening" { "Websites-AxyLusion-Refresh-Evening" }
    default { throw "Unsupported mode: $Mode" }
}

$refreshArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $refreshScript
)

if ($Mode -eq "Evening") {
    $refreshArgs += "-SkipAList"
}

Push-Location $projectRoot
try {
    & $runLogged -Name $taskName -Exe "powershell.exe" -Args $refreshArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
