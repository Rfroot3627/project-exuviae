# scripts/run_hub_local.ps1
# Run Hub bound to 0.0.0.0 to allow LAN access (e.g., from a Raspberry Pi)
# This script is for local development and remains untracked in terms of specific IPs.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$hubDir = Join-Path $repoRoot "hub"
$hubPy = Join-Path $hubDir ".venv\Scripts\python.exe"

if (-not (Test-Path $hubPy)) {
    Write-Host "[Error] Hub venv not found at $hubPy" -ForegroundColor Red
    Write-Host "Please run scripts/check.ps1 first to ensure environment is ready."
    exit 1
}

Write-Host "== Starting Hub on 0.0.0.0 (LAN Access Mode) ==" -ForegroundColor Cyan
Write-Host "Repo Root: $repoRoot"
Write-Host "Hub Dir:   $hubDir"

# Bind to 0.0.0.0 to listen on all network interfaces
# Use --reload for development convenience
Push-Location $hubDir
try {
    & $hubPy -m uvicorn exuviae_hub.main:app --host 0.0.0.0 --port 8000 --reload
} finally {
    Pop-Location
}
