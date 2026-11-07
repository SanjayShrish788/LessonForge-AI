# Orchestrate a live acceptance run: start FastAPI, wait for health,
# run scripts/live_acceptance.py against real providers, then stop the server.
# Never prints API keys. The runner writes progress to stderr on per-case
# failure, so we scope Stop to commands (not native output) and check exit codes.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$py = Join-Path $root 'backend\.venv\Scripts\python.exe'
$outDir = Join-Path $root 'artifacts\openai-acceptance'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$logOut = Join-Path $root 'artifacts\uvicorn.out.log'
$logErr = Join-Path $root 'artifacts\uvicorn.err.log'
$server = Start-Process -FilePath $py `
    -ArgumentList '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000' `
    -WorkingDirectory (Join-Path $root 'backend') -PassThru `
    -RedirectStandardOutput $logOut -RedirectStandardError $logErr

$original = $ErrorActionPreference
try {
    $healthy = $false
    for ($i = 0; $i -lt 40; $i++) {
        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 3
            $healthy = $true
            break
        } catch { Start-Sleep -Seconds 1 }
    }
    if (-not $healthy) { throw 'Backend did not become healthy in time.' }
    Write-Output ('HEALTH: ' + ($health.providers | ConvertTo-Json -Compress))

    $ErrorActionPreference = 'Continue'
    & $py (Join-Path $root 'scripts\live_acceptance.py') `
        --base-url 'http://127.0.0.1:8000/api' --output $outDir --timeout 900
    $code = $LASTEXITCODE
    Write-Output ('ACCEPTANCE_EXIT: ' + $code)
} finally {
    $ErrorActionPreference = $original
    if ($server -and -not $server.HasExited) { Stop-Process -Id $server.Id -Force }
}

