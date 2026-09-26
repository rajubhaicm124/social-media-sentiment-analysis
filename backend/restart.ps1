# Restart the dev API and wait until /api/health responds.
param([int]$Port = 8000)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like "*uvicorn*app.main:app*$Port*" } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Start-Sleep -Seconds 1
Start-Process -FilePath '.\.venv\Scripts\python.exe' `
  -ArgumentList '-m', 'uvicorn', 'app.main:app', '--port', $Port `
  -RedirectStandardOutput 'server.log' -RedirectStandardError 'server.err' -NoNewWindow

for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Milliseconds 700
  try {
    $null = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 3
    Write-Host "API ready on port $Port"
    exit 0
  } catch { }
}
Write-Host "API failed to start. Last errors:"
Get-Content 'server.err' -ErrorAction SilentlyContinue | Select-Object -Last 25
exit 1
