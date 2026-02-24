# scripts/verify_hub_node_registry.ps1
# Verification for Hub Node Registry (Persistent in Memory)

$ErrorActionPreference = "Stop"

# 1. Setup Environment
$HubPort = 8000
$HubUrl = "http://localhost:$HubPort"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$HubDir = Join-Path $RepoRoot "hub"
$NodeDir = Join-Path $RepoRoot "node"

Write-Host "== Starting Hub Node Registry Verification ==" -ForegroundColor Cyan

# 2. Start Hub (Background)
Write-Host "Starting Hub..."
$HubPython = Join-Path $HubDir ".venv\Scripts\python.exe"
$HubProcess = Start-Process -FilePath $HubPython -ArgumentList "-m uvicorn exuviae_hub.main:app --port $HubPort" -WorkingDirectory $HubDir -PassThru -NoNewWindow
Start-Sleep -Seconds 5

# 3. Start Node (Background)
Write-Host "Starting Node..."
$NodePython = Join-Path $NodeDir ".venv\Scripts\python.exe"
$NodeSrc = Join-Path $NodeDir "src"
$NodeProcess = Start-Process -FilePath $NodePython -ArgumentList "-m exuviae_node.main" -WorkingDirectory $NodeSrc -PassThru -NoNewWindow
Start-Sleep -Seconds 5

try {
    # 4. Query Hub for registered nodes
    Write-Host "Querying /api/v0/nodes..."
    $Response = Invoke-RestMethod -Uri "$HubUrl/api/v0/nodes" -Method Get
    
    if ($Response.ok -eq $true) {
        $Nodes = $Response.nodes
        if ($Nodes.Count -gt 0) {
            Write-Host "SUCCESS: Found $($Nodes.Count) registered node(s)." -ForegroundColor Green
            $Nodes | ForEach-Object {
                Write-Host " - Node ID: $($_.node_id) (Kind: $($_.kind), Firmware: $($_.firmware))"
            }
        } else {
            Write-Host "ERROR: No nodes found in registry." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "ERROR: API response status 'ok' is not true." -ForegroundColor Red
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
