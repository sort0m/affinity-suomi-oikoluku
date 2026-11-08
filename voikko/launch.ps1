param([ValidateSet('start','stop','status')][string]$Action = 'start')
$ErrorActionPreference = 'Stop'
$candidates = @()
if ($env:VOIKKO_PYTHON) { $candidates += $env:VOIKKO_PYTHON }
# Python bundled with Codex is usable without a separate installation.
$candidates += Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$candidates += @(Get-Command python.exe -All -ErrorAction SilentlyContinue | ForEach-Object Source)
$candidates += @(Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe" -ErrorAction SilentlyContinue | ForEach-Object FullName)
$pythonExe = $null
foreach ($candidate in $candidates | Select-Object -Unique) {
    if (-not (Test-Path -LiteralPath $candidate) -or $candidate -like '*\WindowsApps\*') { continue }
    & $candidate -c 'import sys,struct; sys.exit(0 if sys.version_info >= (3,9) and struct.calcsize(chr(80)) == 8 else 1)' 2>$null
    if ($LASTEXITCODE -eq 0) { $pythonExe = $candidate; break }
}
if (-not $pythonExe) { throw '64-bit Python 3.9+ not found. Install Python or set VOIKKO_PYTHON to its python.exe path.' }
& $pythonExe (Join-Path $PSScriptRoot 'manage.py') $Action
if ($LASTEXITCODE -ne 0) { throw 'Affinity-oikoluvun komento ei onnistunut.' }
