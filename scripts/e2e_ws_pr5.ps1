# scripts/e2e_ws_pr5.ps1
# E2E Smoke Test for WS Command -> Node Capture -> Hub Upload

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$hubDir = Join-Path $repoRoot "hub"
$nodeDir = Join-Path $repoRoot "node"
$hubPy = Join-Path $hubDir ".venv\Scripts\python.exe"
$nodePy = Join-Path $nodeDir ".venv\Scripts\python.exe"

Write-Host "== WS E2E Smoke Start ==" -ForegroundColor Cyan

# 1. Start Hub
Write-Host "[1/5] Starting Hub..."
$hubProcess = Start-Process -FilePath $hubPy -ArgumentList "-m", "uvicorn", "exuviae_hub.main:app", "--port", "8000" -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 5

# 2. Start Node WS Client
Write-Host "[2/5] Starting Node WS Client..."
$env:HUB_WS_URL = "ws://127.0.0.1:8000/ws/v0?node_id=e2e-node-01"
$nodeProcess = Start-Process -FilePath $nodePy -ArgumentList (Join-Path $nodeDir "scripts\ws_node_smoke.py") -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 3

try {
    # 3. Trigger WS Command
    Write-Host "[3/5] Triggering WS Command..."
    & $nodePy (Join-Path $nodeDir "scripts\trigger_capture_ws.py")
    if ($LASTEXITCODE -ne 0) { throw "Trigger script failed" }

    # 4. Verification
    Write-Host "[4/5] Verifying Result..."
    Start-Sleep -Seconds 3

    # Resolve DATA_ROOT from Hub Config (Default: data)
    # Since we can't easily run python to get config in PS without more logic, 
    # we assume 'data' or allow HUB_DATA_ROOT env.
    $dataRoot = if ($env:EXUVIAE_DATA_ROOT) { $env:EXUVIAE_DATA_ROOT } else { Join-Path $hubDir "data" }
    $visionLog = Join-Path $dataRoot "logs\vision.jsonl"

    if (-not (Test-Path $visionLog)) {
        throw "Vision log NOT found at $visionLog"
    }

    $lastLine = Get-Content $visionLog -Tail 1 | ConvertFrom-Json
    $snapshotId = $lastLine.snapshot_id
    $imagePathRelative = $lastLine.image_path

    Write-Host "Found Snapshot ID: $snapshotId"
    Write-Host "Image Path in log: $imagePathRelative"

    # In Hub, image_path is relative to CWD (usually hub/) or data_root?
    # Based on current Hub implementation, it's relative to CWD.
    $imagePathFull = Join-Path $hubDir $imagePathRelative

    if (Test-Path $imagePathFull) {
        Write-Host "✅ VERIFIED: Image file exists at $imagePathFull" -ForegroundColor Green
    } else {
        throw "Verification FAILED: Image file NOT found at $imagePathFull"
    }

} finally {
    # 5. Cleanup
    Write-Host "[5/5] Cleaning up processes..."
    if ($null -ne $hubProcess) { Stop-Process -Id $hubProcess.Id -Force -ErrorAction SilentlyContinue }
    if ($null -ne $nodeProcess) { Stop-Process -Id $nodeProcess.Id -Force -ErrorAction SilentlyContinue }
}

Write-Host "== WS E2E Smoke Success ==" -ForegroundColor Green
