# scripts/verify_node_capture_local.ps1
# End-to-End Verification for Node Camera Capture (Mock Mode on Windows)

$ErrorActionPreference = "Stop"

# 1. Setup Environment
$HubPort = 8000
$HubUrl = "http://localhost:$HubPort"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$HubDir = Join-Path $RepoRoot "hub"
$NodeDir = Join-Path $RepoRoot "node"

Write-Host "== Starting E2E Capture Verification ==" -ForegroundColor Cyan

# 2. Start Hub (Background)
Write-Host "Starting Hub..."
$HubPython = Join-Path $HubDir ".venv\Scripts\python.exe"
$HubProcess = Start-Process -FilePath $HubPython -ArgumentList "-m uvicorn exuviae_hub.main:app --port $HubPort" -WorkingDirectory $HubDir -PassThru -NoNewWindow
Start-Sleep -Seconds 5

# 3. Start Node (Background)
Write-Host "Starting Node (Real App)..."
$NodePython = Join-Path $NodeDir ".venv\Scripts\python.exe"
# Ensure PYTHONPATH includes src
$NodeEnv = @{ PYTHONPATH = (Join-Path $NodeDir "src") }
# Start-Process doesn't easily support env vars in PS Core < 7. 
# We'll rely on running python from src dir or module resolution if installed via pip -e.
# But let's assume we need to set PYTHONPATH or run from src. 
# Better: Run from node root, but -m exuviae_node needs it in path.
# Let's use cmd /c to set env, or assume standard structure
# If not installed, we need to set PYTHONPATH.
# Powershell Start-Process -Environment is available in newer PS. 
# Fallback: create a temporary wrapper script or assume installed?
# Let's try running from src folder.
$NodeSrc = Join-Path $NodeDir "src"
$NodeProcess = Start-Process -FilePath $NodePython -ArgumentList "-m exuviae_node.main" -WorkingDirectory $NodeSrc -PassThru -NoNewWindow
Start-Sleep -Seconds 5

try {
    # 4. Trigger Capture via Hub API
    Write-Host "Triggering Capture via API..."
    $Payload = @{ node_id = "test-node-01" } | ConvertTo-Json
    $Response = Invoke-RestMethod -Uri "$HubUrl/api/v0/capture" -Method Post -Body $Payload -ContentType "application/json"
    
    $SnapshotId = $Response.snapshot_id
    Write-Host "Capture Requested. Snapshot ID: $SnapshotId" -ForegroundColor Green

    # 5. Wait for Upload (Mock capture is fast, but network/process overhead)
    Write-Host "Waiting for upload..."
    $MaxRetries = 10
    $Found = $false
    
    for ($i = 0; $i -lt $MaxRetries; $i++) {
        Start-Sleep -Seconds 1
        # Check Hub Data Dir
        # Data root is 'data' relative to Hub CWD usually.
        $DateStr = Get-Date -Format "yyyy-MM-dd"
        $SearchPath = Join-Path $HubDir "data\snapshots\$DateStr\test-node-01\$SnapshotId.jpg"
        
        # Node ID might be from config... Node default config loads default.yaml => node_id: "node-001" usually?
        # Let's check default.yaml or just wildcard search
        $WildcardPath = Join-Path $HubDir "data\snapshots\$DateStr\*\$SnapshotId.jpg"
        
        if (Test-Path $WildcardPath) {
            Write-Host "SUCCESS: Snapshot found at $WildcardPath" -ForegroundColor Green
            $Found = $true
            break
        }
    }

    if (-not $Found) {
        Write-Host "ERROR: Snapshot file not found after waiting." -ForegroundColor Red
        exit 1
    }

} catch {
    Write-Host "Test Failed: $_" -ForegroundColor Red
    exit 1
} finally {
    # Cleanup
    Write-Host "Stopping processes..."
    Stop-Process -Id $NodeProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $HubProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "Done."
}
