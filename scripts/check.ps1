# scripts/check.ps1
param(
  [switch]$E2E,
  [switch]$E2EWS
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-LastExitCode([string]$what) {
  if ($LASTEXITCODE -ne 0) {
    throw "$what failed (exit code=$LASTEXITCODE)"
  }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$hubDir   = Join-Path $repoRoot "hub"
$hubPy    = Join-Path $hubDir ".venv\Scripts\python.exe"

Write-Host "== (0) Environment ==" -ForegroundColor Cyan
Write-Host "repoRoot: $repoRoot"
Write-Host "hubDir  : $hubDir"
Write-Host "hubPy   : $hubPy"

if (-not (Test-Path $hubPy)) {
  throw "hub venv python not found: $hubPy (請先在 hub 建好 .venv 或跑過 e2e_pr4.ps1 一次)"
}

Write-Host "`n== (1) Contract/Spec checks (root) ==" -ForegroundColor Cyan
# 依你的專案實際入口調整：這裡只做「存在就跑」的保守策略
$specCandidates = @(
  (Join-Path $repoRoot "tool\verify_all.py"),
  (Join-Path $repoRoot "tool\verify_contracts.py"),
  (Join-Path $repoRoot "system\verify_all.ps1"),
  (Join-Path $repoRoot "system\verify_contracts.ps1")
)

$ranSpec = $false
foreach ($c in $specCandidates) {
  if (Test-Path $c) {
    $ranSpec = $true
    if ($c.EndsWith(".py")) {
      python $c
      Assert-LastExitCode "Spec check ($c)"
    } else {
      powershell -ExecutionPolicy Bypass -File $c
      Assert-LastExitCode "Spec check ($c)"
    }
    break
  }
}

if (-not $ranSpec) {
  Write-Host "(!) 找不到 root 規格驗證入口（未執行）。你可在 scripts/check.ps1 補上你的實際命令。" -ForegroundColor Yellow
}

Write-Host "`n== (2) Hub fast tests (pytest, not e2e) ==" -ForegroundColor Cyan
Push-Location $hubDir
try {
  & $hubPy -m pytest -q -m "not e2e"
  Assert-LastExitCode "Hub fast tests (pytest)"
} finally {
  Pop-Location
}

if ($E2E) {
  Write-Host "`n== (3) PR4 E2E smoke ==" -ForegroundColor Cyan
  powershell -ExecutionPolicy Bypass -File (Join-Path $repoRoot "scripts\e2e_pr4.ps1")
  Assert-LastExitCode "PR4 E2E smoke"
}

if ($E2EWS) {
  Write-Host "`n== (4) WS E2E smoke ==" -ForegroundColor Cyan
  powershell -ExecutionPolicy Bypass -File (Join-Path $repoRoot "scripts\e2e_ws_pr5.ps1")
  Assert-LastExitCode "WS E2E smoke"
}

Write-Host "`n✅ CHECK OK" -ForegroundColor Green
