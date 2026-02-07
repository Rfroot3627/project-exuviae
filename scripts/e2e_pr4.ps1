# scripts\e2e_pr4.ps1
# E2E Smoke Test for PR4: Capture -> Upload(persist) -> Logline
# Windows PowerShell / PowerShell 7 compatible.
# Key goals:
# - Run hub using hub/.venv (not base)
# - Avoid pipeline pollution from pip outputs (no "second truth")
# - Capture hub stdout/stderr to files; dump on timeout for debugging

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Repo-Root {
  $scriptsDir = $PSScriptRoot
  if (-not $scriptsDir) {
    throw "PSScriptRoot is empty. Please run via: powershell -File .\scripts\e2e_pr4.ps1"
  }
  return (Resolve-Path (Join-Path $scriptsDir "..")).Path
}

function Invoke-Native-NoPipeline([string]$exe, [string[]]$args, [string]$workdir) {
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $exe
  $psi.WorkingDirectory = $workdir
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError  = $true

  foreach ($a in $args) { [void]$psi.ArgumentList.Add($a) }

  $p = New-Object System.Diagnostics.Process
  $p.StartInfo = $psi

  if (-not $p.Start()) {
    throw "Failed to start: $exe"
  }

  $stdout = $p.StandardOutput.ReadToEnd()
  $stderr = $p.StandardError.ReadToEnd()
  $p.WaitForExit()

  if ($stdout) { Write-Host $stdout }
  if ($stderr) { Write-Host $stderr }

  if ($p.ExitCode -ne 0) {
    throw "Command failed (exit=$($p.ExitCode)): $exe $($args -join ' ')"
  }

  # IMPORTANT: do not output anything to pipeline from this function
  return
}

function Ensure-Hub-Venv-And-Install([string]$hubDir) {
  $venvPython = Join-Path $hubDir ".venv\Scripts\python.exe"
  $venvPip    = Join-Path $hubDir ".venv\Scripts\pip.exe"

  if (-not (Test-Path $venvPython)) {
    Write-Host "[hub] .venv not found, creating venv..." -ForegroundColor Cyan
    Invoke-Native-NoPipeline -exe "python" -args @("-m","venv",".venv") -workdir $hubDir
  }

  Write-Host "[hub] Installing hub (editable) + test deps..." -ForegroundColor Cyan
  Invoke-Native-NoPipeline -exe $venvPip -args @("install","-e",".[test]") -workdir $hubDir
  
  Write-Host "[hub] Ensuring uvicorn is installed..." -ForegroundColor Cyan
  Invoke-Native-NoPipeline -exe $venvPip -args @("install","uvicorn") -workdir $hubDir

  if (-not (Test-Path $venvPython)) {
    throw "hub venv python not found: $venvPython"
  }

  # Return EXACTLY one clean string
  return $venvPython
}

function Start-Hub([string]$hubDir, [string]$venvPython) {
  Write-Host "[hub] Starting hub server (uvicorn)..." -ForegroundColor Cyan

  $stdout = Join-Path $hubDir ".e2e_hub_stdout.log"
  $stderr = Join-Path $hubDir ".e2e_hub_stderr.log"
  Remove-Item -ErrorAction SilentlyContinue $stdout, $stderr

  # 用 uvicorn 啟動，不依賴 exuviae_hub.main 內部是否有 run()
  return Start-Process -FilePath $venvPython `
                       -ArgumentList @(
                         "-m","uvicorn",
                         "exuviae_hub.main:app",
                         "--host","127.0.0.1",
                         "--port","8000",
                         "--log-level","info"
                       ) `
                       -WorkingDirectory $hubDir `
                       -PassThru `
                       -NoNewWindow `
                       -RedirectStandardOutput $stdout `
                       -RedirectStandardError  $stderr
}


function Dump-Hub-Logs([string]$hubDir) {
  $stdout = Join-Path $hubDir ".e2e_hub_stdout.log"
  $stderr = Join-Path $hubDir ".e2e_hub_stderr.log"

  Write-Host "`n[hub] Dumping hub logs (tail 200):" -ForegroundColor Yellow
  if (Test-Path $stdout) {
    Write-Host "---- STDOUT ----" -ForegroundColor Yellow
    Get-Content -LiteralPath $stdout -Tail 200 | Out-Host
  } else {
    Write-Host "---- STDOUT ---- (missing)" -ForegroundColor Yellow
  }

  if (Test-Path $stderr) {
    Write-Host "---- STDERR ----" -ForegroundColor Yellow
    Get-Content -LiteralPath $stderr -Tail 200 | Out-Host
  } else {
    Write-Host "---- STDERR ---- (missing)" -ForegroundColor Yellow
  }
}

function Wait-Http([string]$url, [int]$timeoutSec, [string]$hubDir, $proc) {
  Write-Host "[wait] Waiting for $url ..." -ForegroundColor Cyan
  $sw = [System.Diagnostics.Stopwatch]::StartNew()

  while ($sw.Elapsed.TotalSeconds -lt $timeoutSec) {
    if ($proc -and $proc.HasExited) {
      Write-Host "[wait] Hub process exited early." -ForegroundColor Yellow
      break
    }
    try {
      $null = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
      Write-Host "[wait] Ready." -ForegroundColor Green
      return
    } catch {
      Start-Sleep -Milliseconds 400
    }
  }

  Dump-Hub-Logs -hubDir $hubDir
  throw "Timeout waiting for hub at $url"
}

function Get-LogPath([string]$hubDir, [string]$venvPython) {
  # Use hub settings to compute JSONL path (no hardcoded templates)
  $code = @"
from exuviae_hub.infrastructure.config import settings
from pathlib import Path
p = Path(settings.DATA_ROOT) / settings.LOG_SUBDIR / settings.VISION_LOG_FILENAME
print(str(p))
"@

  # IMPORTANT: use the clean venv python path
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $venvPython
  $psi.WorkingDirectory = $hubDir
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError  = $true
  # 用 -c "...." 需要把換行與引號處理好：最穩是把 code 寫到暫存檔再執行
  $tmp = Join-Path $hubDir ".e2e_tmp_get_log_path.py"
  Set-Content -LiteralPath $tmp -Value $code -Encoding UTF8
  $psi.Arguments = "`"$tmp`""


  $p = New-Object System.Diagnostics.Process
  $p.StartInfo = $psi
  [void]$p.Start()
  $stdout = $p.StandardOutput.ReadToEnd()
  $stderr = $p.StandardError.ReadToEnd()
  $p.WaitForExit()
  if ($p.ExitCode -ne 0) {
    Write-Host $stderr
    throw "Get-LogPath failed"
  }

  $logPath = $stdout.Trim()
  if (-not [System.IO.Path]::IsPathRooted($logPath)) {
    $logPath = (Resolve-Path (Join-Path $hubDir $logPath)).Path
  }
  return $logPath
}

function Get-DataRoot([string]$hubDir, [string]$venvPython) {
  $code = @"
from exuviae_hub.infrastructure.config import settings
from pathlib import Path
print(str(Path(settings.DATA_ROOT)))
"@

  $tmp = Join-Path $hubDir ".e2e_tmp_get_data_root.py"
  Set-Content -LiteralPath $tmp -Value $code -Encoding UTF8

  try {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $venvPython
    $psi.WorkingDirectory = $hubDir
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.Arguments = "`"$tmp`""

    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    [void]$p.Start()
    $stdout = $p.StandardOutput.ReadToEnd()
    $stderr = $p.StandardError.ReadToEnd()
    $p.WaitForExit()

    if ($p.ExitCode -ne 0) {
      if ($stderr) { Write-Host $stderr }
      throw "Get-DataRoot failed"
    }

    $dataRoot = $stdout.Trim()
    if (-not [System.IO.Path]::IsPathRooted($dataRoot)) {
      $dataRoot = (Resolve-Path (Join-Path $hubDir $dataRoot)).Path
    }
    return $dataRoot
  }
  finally {
    Remove-Item -ErrorAction SilentlyContinue $tmp
  }
}


function Get-LogLineCount([string]$path) {
  if (-not (Test-Path $path)) { return 0 }
  return (Get-Content -LiteralPath $path -ErrorAction Stop).Count
}

# ---------------- Main ----------------
$repoRoot = Repo-Root
$hubDir   = Join-Path $repoRoot "hub"
if (-not (Test-Path $hubDir)) { throw "Hub directory not found: $hubDir" }

$hubProc = $null
try {
  $hubPython = Ensure-Hub-Venv-And-Install -hubDir $hubDir

  # Defensive check: ensure hubPython is clean
  if ($hubPython -notmatch "\\hub\\\.venv\\Scripts\\python\.exe$") {
    throw "hubPython looks wrong (polluted?): $hubPython"
  }
  Write-Host "[debug] hub python = $hubPython" -ForegroundColor DarkGray

  $logPath = Get-LogPath -hubDir $hubDir -venvPython $hubPython
  $dataRootAbs = Get-DataRoot -hubDir $hubDir -venvPython $hubPython
  Write-Host "[info] Data root: $dataRootAbs" -ForegroundColor DarkGray

  $beforeLogCount = Get-LogLineCount -path $logPath
  Write-Host "[info] Log path: $logPath" -ForegroundColor DarkGray
  Write-Host "[info] Log lines before: $beforeLogCount" -ForegroundColor DarkGray

  $hubProc = Start-Hub -hubDir $hubDir -venvPython $hubPython
  Wait-Http -url "http://127.0.0.1:8000/docs" -timeoutSec 35 -hubDir $hubDir -proc $hubProc

  # ---- Step 1: Capture ----
  $nodeId = "cam-test-01"
  $captureBody = @{ node_id = $nodeId } | ConvertTo-Json -Compress
  $cap = Invoke-RestMethod -Method Post `
                           -Uri "http://127.0.0.1:8000/api/v0/capture" `
                           -Body $captureBody `
                           -ContentType "application/json"
  if (-not $cap.snapshot_id) { throw "capture response missing snapshot_id" }
  $sid = $cap.snapshot_id
  Write-Host "[ok] capture snapshot_id = $sid" -ForegroundColor Green

  # ---- Step 2: Upload (use python requests inside hub venv) ----
  $uploadCode = @"
import requests
node_id = r'''$nodeId'''
snapshot_id = r'''$sid'''
jpeg = b'\xff\xd8' + b'\x00'*10 + b'\xff\xd9'
r = requests.post(
  'http://127.0.0.1:8000/api/v0/snapshots/upload',
  data={'node_id': node_id, 'snapshot_id': snapshot_id},
  files={'image': ('t.jpg', jpeg, 'image/jpeg')},
  timeout=10
)
print(r.status_code)
print(r.text)
"@

  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $hubPython
  $psi.WorkingDirectory = $hubDir
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError  = $true
  $tmp = Join-Path $hubDir ".e2e_tmp_upload.py"
  Set-Content -LiteralPath $tmp -Value $uploadCode -Encoding UTF8
  $psi.Arguments = "`"$tmp`""

  $p = New-Object System.Diagnostics.Process
  $p.StartInfo = $psi
  [void]$p.Start()
  $stdout = $p.StandardOutput.ReadToEnd()
  $stderr = $p.StandardError.ReadToEnd()
  $p.WaitForExit()
  if ($p.ExitCode -ne 0) {
    Write-Host $stderr
    throw "upload subprocess failed"
  }

  $lines = $stdout -split "`r?`n"
  $status = [int]$lines[0]
  if ($status -lt 200 -or $status -ge 300) {
    throw "upload failed, status=$status`n$stdout"
  }

  $jsonText = ($lines[1..($lines.Length-1)] -join "`n").Trim()
  $uploadResp = $jsonText | ConvertFrom-Json
  if (-not $uploadResp.image_path) { throw "upload response missing image_path`n$jsonText" }
  Write-Host "[ok] upload ok, image_path = $($uploadResp.image_path)" -ForegroundColor Green

  # ---- Step 3: Verify file exists ----
  # Resolve stored image path against settings.DATA_ROOT (avoid hardcoding repo layout)
  $imagePathRel = $uploadResp.image_path
  $norm = $imagePathRel.Replace('\','/')

  if ([System.IO.Path]::IsPathRooted($imagePathRel)) {
    $imageAbs = $imagePathRel
  } else {
    # Contract uses "data/..." as a logical prefix; map it under DATA_ROOT
    if ($norm.StartsWith("data/")) { $norm = $norm.Substring(5) }
    $imageAbs = Join-Path $dataRootAbs ($norm -replace '/','\')
  }
  if (-not (Test-Path $imageAbs)) {
    throw "stored image not found: $imageAbs (from image_path=$imagePathRel)"
  }
  Write-Host "[ok] stored file exists: $imageAbs" -ForegroundColor Green

  # ---- Step 4: Verify JSONL +1 ----
  $afterLogCount = Get-LogLineCount -path $logPath
  Write-Host "[info] Log lines after: $afterLogCount" -ForegroundColor DarkGray
  if ($afterLogCount -ne ($beforeLogCount + 1)) {
    throw "expected log lines +1, before=$beforeLogCount after=$afterLogCount (logPath=$logPath)"
  }
  Write-Host "[ok] JSONL appended (+1 line)" -ForegroundColor Green

  # ---- Step 5: Verify correlation ----
  $last = (Get-Content -LiteralPath $logPath | Select-Object -Last 1) | ConvertFrom-Json
  if ($last.snapshot_id -ne $sid) { throw "last logline snapshot_id mismatch" }
  if ($last.image_path -ne $imagePathRel) { throw "last logline image_path mismatch" }
  if ($last.node_id -ne $nodeId) { throw "last logline node_id mismatch" }
  Write-Host "[ok] logline correlates snapshot_id/node_id/image_path" -ForegroundColor Green

  Write-Host "`n✅ PR4 E2E smoke passed." -ForegroundColor Green
}
finally {
  if ($hubProc -and -not $hubProc.HasExited) {
    Write-Host "[hub] Stopping hub server (pid=$($hubProc.Id))..." -ForegroundColor Cyan
    try { Stop-Process -Id $hubProc.Id -Force } catch {}
  }
}