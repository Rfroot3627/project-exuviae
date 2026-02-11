# ops/windows/hub_firewall.ps1
# Hub Firewall Management Script (Strict SSOT)
# Supports: status, open, close

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RULE_NAME = "exuviae-hub-allow-pi"
$ENV_FILE = Join-Path $PSScriptRoot "..\..\.agent\local\ops.env"

function Get-OpsConfig {
    if (-not (Test-Path $ENV_FILE)) {
        Write-Host "[ERROR] Configuration file not found: $ENV_FILE" -ForegroundColor Red
        Write-Host "Please 'cp .agent/local/ops.env.example .agent/local/ops.env' and fill it."
        exit 1
    }
    $config = @{}
    Get-Content $ENV_FILE | Where-Object { $_ -match "=" } | ForEach-Object {
        $parts = $_ -split "=", 2
        $config[$parts[0].Trim()] = $parts[1].Trim()
    }
    return $config
}

function Show-Status {
    Write-Host "== (OS) Windows Network Profiles ==" -ForegroundColor Cyan
    $profiles = Get-NetConnectionProfile
    $ips = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.PrefixOrigin -ne "WellKnown" }
    
    foreach ($p in $profiles) {
        $ifAlias = $p.InterfaceAlias
        $cat = $p.NetworkCategory
        $matchIps = $ips | Where-Object { $_.InterfaceAlias -eq $ifAlias } | ForEach-Object { $_.IPAddress }
        $ipStr = $matchIps -join ", "
        
        $color = if ($cat -eq "Public") { "Yellow" } else { "Green" }
        Write-Host "Interface: $ifAlias"
        Write-Host "  IPs:      $ipStr"
        Write-Host "  Category: $cat" -ForegroundColor $color
    }

    Write-Host "`n== (Rule) Firewall Status: $RULE_NAME ==" -ForegroundColor Cyan
    $rule = Get-NetFirewallRule -Name $RULE_NAME -ErrorAction SilentlyContinue
    if ($null -eq $rule) {
        Write-Host "Rule does not exist." -ForegroundColor Gray
    } else {
        $filter = Get-NetFirewallPortFilter -Name $RULE_NAME
        $addressFilter = Get-NetFirewallAddressFilter -Name $RULE_NAME
        
        $enabled = $rule.Enabled
        $enabledColor = if ($enabled -eq "True") { "Green" } else { "Red" }
        
        Write-Host "Status:         " -NoNewline; Write-Host "$enabled" -ForegroundColor $enabledColor
        Write-Host "Local Port:     $($filter.LocalPort)"
        Write-Host "Remote Address: $($addressFilter.RemoteAddress)"
    }

    Write-Host "`n[Note] NetworkCategory is for reference. Security boundary is defined by RemoteAddress restriction." -ForegroundColor Gray
}

function Open-Firewall {
    $cfg = Get-OpsConfig
    $piIp = $cfg["PI_IP"]
    $port = $cfg["HUB_PORT"]

    if ([string]::IsNullOrWhiteSpace($piIp) -or [string]::IsNullOrWhiteSpace($port)) {
        Write-Host "[ERROR] Missing PI_IP or HUB_PORT in $ENV_FILE" -ForegroundColor Red
        exit 1
    }

    Write-Host "== Opening Firewall for Pi ($piIp) on Port $port ==" -ForegroundColor Cyan
    
    $ruleParams = @{
        DisplayName = "Exuviae Hub: Allow Pi Node"
        Name = $RULE_NAME
        Description = "Allow incoming traffic from Raspberry Pi Node to Exuviae Hub"
        Direction = "Inbound"
        Protocol = "TCP"
        LocalPort = $port
        RemoteAddress = $piIp
        Action = "Allow"
        Enabled = "True"
    }

    try {
        if (Get-NetFirewallRule -Name $RULE_NAME -ErrorAction SilentlyContinue) {
            Set-NetFirewallRule @ruleParams
            Write-Host "Rule updated and enabled." -ForegroundColor Green
        } else {
            New-NetFirewallRule @ruleParams
            Write-Host "New rule created and enabled." -ForegroundColor Green
        }
    } catch {
        Write-Host "[WARNING] Failed to apply firewall rule. Reason: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "TIP: This action requires Administrator privileges. Please run as Admin or use 'elevated_firewall_run.ps1'." -ForegroundColor White
    }
}

function Close-Firewall {
    Write-Host "== Closing Firewall Rule: $RULE_NAME ==" -ForegroundColor Cyan
    try {
        if (Get-NetFirewallRule -Name $RULE_NAME -ErrorAction SilentlyContinue) {
            Disable-NetFirewallRule -Name $RULE_NAME
            Write-Host "Rule disabled." -ForegroundColor Yellow
        } else {
            Write-Host "Rule not found. Nothing to close." -ForegroundColor Gray
        }
    } catch {
        Write-Host "[WARNING] Failed to close firewall rule. Reason: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "TIP: This action requires Administrator privileges." -ForegroundColor White
    }
}

# --- Main ---
$cmd = if ($args.Count -gt 0) { $args[0].ToLower() } else { "status" }

switch ($cmd) {
    "status" { Show-Status }
    "open"   { Open-Firewall }
    "close"  { Close-Firewall }
    default  {
        Write-Host "Usage: .\hub_firewall.ps1 [status | open | close]"
    }
}
