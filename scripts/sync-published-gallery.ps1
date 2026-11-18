param(
    [string]$Python = "python",
    [string]$DbPath = $env:UNIVERSAL_DB_PATH,
    [switch]$Apply,
    [switch]$SkipCheckpoint
)

if (-not $DbPath) {
    throw "Set UNIVERSAL_DB_PATH or pass -DbPath: the database lives in a private local workspace."
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExportScript = Join-Path $ScriptDir "export-published-gallery.py"

$Args = @($ExportScript, "--db", $DbPath)

if ($Apply) {
    $Args += "--apply"
}

if ($SkipCheckpoint) {
    $Args += "--skip-checkpoint"
}

& $Python @Args
exit $LASTEXITCODE
