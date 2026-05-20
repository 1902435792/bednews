param (
    [string]$Topic,
    [string]$Category = "Uncategorized",
    [string]$Date,
    [switch]$NoVisual
)

# Tiny wrapper to delegate to python archiver.py (to prevent CP936/GBK encoding bugs)
$ScriptPath = Join-Path $PSScriptRoot "archiver.py"
$ArgsList = @("--topic", $Topic, "--category", $Category)

if ($Date) {
    $ArgsList += @("--date", $Date)
}
if ($NoVisual) {
    $ArgsList += "--no-visual"
}

python $ScriptPath $ArgsList
