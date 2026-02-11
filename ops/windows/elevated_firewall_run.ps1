# ops/windows/elevated_firewall_run.ps1
# Helper script to run hub_firewall.ps1 with Administrator privileges

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$firewallScript = Join-Path $PSScriptRoot "hub_firewall.ps1"

Write-Host "== Requesting Elevated Privileges to Manage Firewall ==" -ForegroundColor Cyan
Write-Host "This will open a new PowerShell window with UAC prompt."

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "powershell.exe"
$psi.Arguments = "-NoExit -ExecutionPolicy Bypass -File `"$firewallScript`" status; Write-Host '--- Elevated Session Active ---' -ForegroundColor Cyan"
$psi.Verb = "runas" # This triggers the UAC prompt

try {
    [System.Diagnostics.Process]::Start($psi)
    Write-Host "Elevated window should now be open." -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to start elevated session: $($_.Exception.Message)" -ForegroundColor Red
}
