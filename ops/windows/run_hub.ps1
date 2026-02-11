# ops/windows/run_hub.ps1
# Start Hub with 0.0.0.0 binding (Strict SSOT)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$hubDir = Join-Path $repoRoot "hub"
$hubPy = Join-Path $hubDir ".venv\Scripts\python.exe"
$ENV_FILE = Join-Path $PSScriptRoot "..\..\.agent\local\ops.env"

if (-not (Test-Path $hubPy)) {
    Write-Host "[Error] Hub venv not found at $hubPy" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $ENV_FILE)) {
    Write-Host "[ERROR] Configuration file not found: $ENV_FILE" -ForegroundColor Red
    Write-Host "Please 'cp .agent/local/ops.env.example .agent/local/ops.env' and fill it."
    exit 1
}

# Read Port from ops.env
$cfg = @{}
Get-Content $ENV_FILE | Where-Object { $_ -match "=" } | ForEach-Object {
    $parts = $_ -split "=", 2
    $cfg[$parts[0].Trim()] = $parts[1].Trim()
}

$port = $cfg["HUB_PORT"]
if ([string]::IsNullOrWhiteSpace($port)) {
    Write-Host "[ERROR] HUB_PORT not defined in $ENV_FILE" -ForegroundColor Red
    exit 1
}

Write-Host "== Starting Hub (LAN Mode) ==" -ForegroundColor Cyan
Write-Host "Binding: 0.0.0.0:$port"

# Show Network Category for the potential LAN interface
$profiles = Get-NetConnectionProfile
$lanP = $profiles | Where-Object { (Get-NetIPAddress -InterfaceAlias $_.InterfaceAlias -AddressFamily IPv4).IPAddress -match "^(192\.168|10\.|172\.(1[6-9]|2[0-9]|3[0-1]))" } | Select-Object -First 1

if ($lanP) {
    Write-Host "LAN Interface: $($lanP.InterfaceAlias) ($($lanP.NetworkCategory))" -ForegroundColor Gray
}

Push-Location $hubDir
try {
    & $hubPy -m uvicorn exuviae_hub.main:app --host 0.0.0.0 --port $port
} finally {
    Pop-Location
}
