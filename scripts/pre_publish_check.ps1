# scripts/pre_publish_check.ps1
# Pre-publish Safety Check for project-exuviae

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue" # Allow script to continue after finding issues

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

Write-Host "== Pre-publish Safety Audit ==" -ForegroundColor Cyan

$issuesFound = 0

# --- 1. Filename Blacklist ---
Write-Host "`n[1/3] Checking for sensitive filenames..." -ForegroundColor Gray
$blacklist = @(
    ".env", "*.env", "*.key", "*.pem", "*.pfx", 
    "id_rsa", "id_ed25519", "authorized_keys",
    "tokens.json", "credentials.json"
)

foreach ($pattern in $blacklist) {
    # Exclude .venv and node_modules from filename scan to avoid noise
    $files = Get-ChildItem -Path . -Filter $pattern -Recurse -File -ErrorAction SilentlyContinue | Where-Object { 
        $_.FullName -notmatch "node_modules" -and $_.FullName -notmatch "\\\.venv\\"
    }
    
    foreach ($file in $files) {
        Write-Host "[CRITICAL] Sensitive file found: $($file.FullName)" -ForegroundColor Red
        $issuesFound++
    }
}

# --- 2. Sensitive Content Patterns ---
Write-Host "`n[2/3] Scanning content for sensitive patterns..." -ForegroundColor Gray
$patterns = @(
    "Bearer ",
    "AKIA[A-Z0-9]{16}", # AWS Access Key
    "BEGIN PRIVATE KEY",
    "BEGIN RSA PRIVATE KEY",
    "secret_key\s*=",
    "api_token\s*="
)

# Use git grep if available as it respects gitignore and is fast
$hasGit = (Get-Command git -ErrorAction SilentlyContinue) -ne $null
if ($hasGit) {
    foreach ($p in $patterns) {
        # --untracked: search in untracked files as well
        # --exclude-standard: use .gitignore etc for untracked files
        $matches = git grep -Ei --untracked --exclude-standard "$p" -- . ":(exclude).venv" ":(exclude)node_modules" ":(exclude)*.ps1" 2>$null
        foreach ($m in $matches) {
            Write-Host "[WARNING] Potential secret pattern found: $m" -ForegroundColor Yellow
            $issuesFound++
        }
    }
} else {
    Write-Host "(!) Git not found, skipping deep content scan. Using basic grep fallback..." -ForegroundColor Yellow
    foreach ($p in $patterns) {
        $files = Get-ChildItem -Path . -Recurse -File | Where-Object { 
            $_.Extension -match "\.(py|md|json|yaml|yml|toml|js|ts)$" -and $_.FullName -notmatch "\\\.venv\\" 
        }
        foreach ($f in $files) {
            if (Select-String -Path $f.FullName -Pattern $p -Quiet) {
                Write-Host "[WARNING] Potential secret pattern found in: $($f.FullName)" -ForegroundColor Yellow
                $issuesFound++
            }
        }
    }
}

# --- 3. Gitignore Verification ---
Write-Host "`n[3/3] Verifying .gitignore coverage..." -ForegroundColor Gray
$criticalPaths = @(
    "hub/data",
    "node/.venv",
    "hub/.venv",
    "hub/data/logs/vision.jsonl",
    "hub/data/snapshots/test.jpg"
)

if ($hasGit) {
    foreach ($path in $criticalPaths) {
        $ignored = git check-ignore -q $path
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[CRITICAL] Path NOT ignored by git: $path" -ForegroundColor Red
            $issuesFound++
        } else {
            Write-Host "  OK: $path is ignored" -ForegroundColor DarkGray
        }
    }
} else {
    Write-Host "(!) Git not found, cannot verify .gitignore effectively." -ForegroundColor Yellow
}

Write-Host "`n----------------------------"
if ($issuesFound -eq 0) {
    Write-Host "✅ Audit PASSED. No obvious sensitive data found." -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Audit FAILED. Found $issuesFound issue(s). Please fix before pushing." -ForegroundColor Red
    exit 1
}
