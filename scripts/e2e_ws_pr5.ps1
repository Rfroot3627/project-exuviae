# scripts/e2e_ws_pr5.ps1
# E2E Smoke Test for WS Command -> Node Capture -> Hub Upload
# Strictly adheres to SSOT by fetching Hub settings dynamically.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Repo-Root {
  return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Wait-Http([string]$url, [int]$timeoutSec) {
  Write-Host "[wait] Waiting for $url ..." -ForegroundColor Cyan
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt $timeoutSec) {
    try {
      $null = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
      Write-Host "[wait] Ready." -ForegroundColor Green
      return
    } catch {
      Start-Sleep -Milliseconds 500
    }
  }
  throw "Timeout waiting for hub at $url"
}

function Get-Hub-Config([string]$hubDir, [string]$hubPy, [string]$pythonCode) {
  $tmp = Join-Path $hubDir ".e2e_ws_tmp_config.py"
  try {
    Set-Content -LiteralPath $tmp -Value $pythonCode -Encoding UTF8
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $hubPy
    $psi.WorkingDirectory = $hubDir
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.Arguments = "`"$tmp`""
    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    [void]$p.Start()
    $stdout = $p.StandardOutput.ReadToEnd()
    $p.WaitForExit()
    if ($p.ExitCode -ne 0) { throw "Failed to get Hub config" }
    return $stdout.Trim()
  } finally {
    Remove-Item -ErrorAction SilentlyContinue $tmp
  }
}

$repoRoot = Repo-Root
$hubDir = Join-Path $repoRoot "hub"
$nodeDir = Join-Path $repoRoot "node"
$hubPy = Join-Path $hubDir ".venv\Scripts\python.exe"
$nodePy = Join-Path $nodeDir ".venv\Scripts\python.exe"

if (-not (Test-Path $hubPy)) { throw "Hub venv not found at $hubPy" }
if (-not (Test-Path $nodePy)) { throw "Node venv not found at $nodePy" }

Write-Host "== WS E2E Smoke Start (SSOT Mode) ==" -ForegroundColor Cyan

# 0. Fetch Dynamic Config
Write-Host "[0/5] Resolving Hub Dynamic Config..."
$pythonGetLog = "from exuviae_hub.infrastructure.config import settings; from pathlib import Path; print(str(Path(settings.DATA_ROOT) / settings.LOG_SUBDIR / settings.VISION_LOG_FILENAME))"
$logicLogPathLower = Get-Hub-Config -hubDir $hubDir -hubPy $hubPy -pythonCode $pythonGetLog
$visionLog = Join-Path $hubDir $logicLogPathLower

$pythonGetDataRoot = "from exuviae_hub.infrastructure.config import settings; print(settings.DATA_ROOT)"
$dataRoot = Get-Hub-Config -hubDir $hubDir -hubPy $hubPy -pythonCode $pythonGetDataRoot
$dataRootAbs = if ([System.IO.Path]::IsPathRooted($dataRoot)) { $dataRoot } else { (Resolve-Path (Join-Path $hubDir $dataRoot)).Path }

Write-Host "Vision Log: $visionLog" -ForegroundColor DarkGray
Write-Host "Data Root : $dataRootAbs" -ForegroundColor DarkGray

$beforeCount = if (Test-Path $visionLog) { (Get-Content $visionLog).Count } else { 0 }

# 1. Start Hub
Write-Host "[1/5] Starting Hub..."
$hubProcess = Start-Process -FilePath $hubPy -ArgumentList "-m", "uvicorn", "exuviae_hub.main:app", "--port", "8000" -PassThru -WindowStyle Hidden -WorkingDirectory $hubDir
Wait-Http -url "http://127.0.0.1:8000/docs" -timeoutSec 15

# 2. Start Node WS Client
Write-Host "[2/5] Starting Node WS Client..."
$env:HUB_WS_URL = "ws://127.0.0.1:8000/ws/v0?node_id=e2e-node-01"
$nodeProcess = Start-Process -FilePath $nodePy -ArgumentList (Join-Path $nodeDir "scripts\ws_node_smoke.py") -PassThru -WindowStyle Hidden -WorkingDirectory $nodeDir
Start-Sleep -Seconds 3

try {
    # 3. Trigger WS Command
    Write-Host "[3/5] Triggering WS Command (using contract example)..."
    & $nodePy (Join-Path $nodeDir "scripts\trigger_capture_ws.py")
    if ($LASTEXITCODE -ne 0) { throw "Trigger script failed" }

    # 4. Verification
    Write-Host "[4/5] Verifying Result..."
    Start-Sleep -Seconds 4

    if (-not (Test-Path $visionLog)) { throw "Vision log NOT found at $visionLog" }
    
    $lines = Get-Content $visionLog
    $afterCount = $lines.Count
    if ($afterCount -le $beforeCount) { throw "Log count did not increase (Before: $beforeCount, After: $afterCount)" }

    $lastLine = $lines[-1] | ConvertFrom-Json
    $snapshotId = $lastLine.snapshot_id
    $imagePathRel = $lastLine.image_path

    Write-Host "Found Snapshot ID: $snapshotId" -ForegroundColor Gray
    
    # Hub stores image_path relative to Hub CWD usually
    $imagePathFull = Join-Path $hubDir $imagePathRel
    if (-not (Test-Path $imagePathFull)) {
        # Fallback check against data_root if relative path in log starts with 'data/'
        if ($imagePathRel.ToLower().StartsWith("data/")) {
            $trimmed = $imagePathRel.Substring(5)
            $imagePathFull = Join-Path $dataRootAbs $trimmed
        }
    }

    if (Test-Path $imagePathFull) {
        Write-Host "✅ VERIFIED: Image file exists at $imagePathFull" -ForegroundColor Green
    } else {
        throw "Verification FAILED: Image file NOT found at $imagePathFull (Log path: $imagePathRel)"
    }

} finally {
    # 5. Cleanup
    Write-Host "[5/5] Cleaning up processes..."
    if ($null -ne $hubProcess) { try { Stop-Process -Id $hubProcess.Id -Force -ErrorAction SilentlyContinue } catch {} }
    if ($null -ne $nodeProcess) { try { Stop-Process -Id $nodeProcess.Id -Force -ErrorAction SilentlyContinue } catch {} }
}

Write-Host "== WS E2E Smoke Success ==" -ForegroundColor Green
