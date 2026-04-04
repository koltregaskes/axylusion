param(
    [string]$Python = "python",
    [string]$DbPath = "W:\Agent Workspace\System\Data\universal.db",
    [switch]$Apply,
    [switch]$SkipCheckpoint
)

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
