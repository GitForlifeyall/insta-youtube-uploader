<#
.SYNOPSIS
    Full Redroid + Instagram Uploader Migration Bundle Creator
.DESCRIPTION
    Packages EVERYTHING needed to run on a new device:
      - Custom WSL2 kernel (bzImage) with Android Binder/BinderFS support
      - .wslconfig (points WSL2 to the custom kernel)
      - All Redroid Docker volumes (per-brand Android data)
      - Full project source code and CLI uploader
    Output: Desktop\redroid_migration_bundle\  and  Desktop\redroid_migration_bundle.zip
.USAGE
    Run in PowerShell (as Administrator recommended):
        .\bundle_export.ps1
#>

$ErrorActionPreference = "Continue"
$Host.UI.RawUI.WindowTitle = "Redroid Migration Bundle Creator"

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
$ProjectRoot   = "C:\Users\khann\OneDrive\Documents\Projects\insta uploader"
$KernelBzImage = "C:\Users\khann\wsl-kernel\bzImage"
$WslConfig     = "C:\Users\khann\.wslconfig"
$OutputDir     = "$env:USERPROFILE\Desktop\redroid_migration_bundle"
$OutputZip     = "$env:USERPROFILE\Desktop\redroid_migration_bundle.zip"

# Auto-detect volumes at runtime -- these are the confirmed existing ones
# Script will also auto-discover any others matching 'redroid-*'
$Volumes = @(
    "redroid-account-01-data",
    "redroid-Account-91-data",
    "redroid-account-01-data-backup",
    "redroid-brand-01-data"
)

# Items to EXCLUDE from project copy (large blobs, cache, git internals)
$ExcludeItems = @(
    "redroid_instagram_complete.zip",
    "__pycache__",
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "*.pyc",
    "*.pyo"
)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
function Write-Step { param([string]$Msg) Write-Host "`n  >> $Msg" -ForegroundColor Cyan }
function Write-Ok   { param([string]$Msg) Write-Host "     OK  $Msg" -ForegroundColor Green }
function Write-Warn { param([string]$Msg) Write-Host "     WARN $Msg" -ForegroundColor Yellow }
function Write-Fail { param([string]$Msg) Write-Host "     FAIL $Msg" -ForegroundColor Red }

function Invoke-Wsl {
    param([string]$Bash)
    # Route stderr to stdout inside bash so PowerShell does not see it as a .NET error
    $result = wsl.exe -d Ubuntu -u root --exec bash -c "($Bash) 2>&1" 2>$null
    return ($result -join "`n") -replace "`0", ""
}

function Format-Bytes {
    param([long]$Bytes)
    if ($Bytes -gt 1GB) { return "{0:N2} GB" -f ($Bytes / 1GB) }
    if ($Bytes -gt 1MB) { return "{0:N2} MB" -f ($Bytes / 1MB) }
    return "{0:N2} KB" -f ($Bytes / 1KB)
}

function Copy-ProjectDir {
    param([string]$Source, [string]$Dest)
    $null = New-Item -ItemType Directory -Path $Dest -Force
    Get-ChildItem -LiteralPath $Source | ForEach-Object {
        $item = $_
        foreach ($ex in $ExcludeItems) {
            if ($item.Name -like $ex) { return }
        }
        if ($item.PSIsContainer) {
            Copy-ProjectDir -Source $item.FullName -Dest (Join-Path $Dest $item.Name)
        } else {
            Copy-Item -LiteralPath $item.FullName -Destination (Join-Path $Dest $item.Name) -Force
        }
    }
}

# ─────────────────────────────────────────────
# START
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "======================================================"
Write-Host "  REDROID MIGRATION BUNDLE CREATOR" -ForegroundColor Magenta
Write-Host "  Kernel + Volumes + Code => one ZIP"
Write-Host "======================================================"
Write-Host ""

# Clean slate
if (Test-Path $OutputDir) {
    Write-Step "Cleaning previous bundle directory..."
    Remove-Item $OutputDir -Recurse -Force
}
if (Test-Path $OutputZip) { Remove-Item $OutputZip -Force }

$null = New-Item -ItemType Directory -Path "$OutputDir\kernel"  -Force
$null = New-Item -ItemType Directory -Path "$OutputDir\volumes" -Force
$null = New-Item -ItemType Directory -Path "$OutputDir\code"    -Force

# ─────────────────────────────────────────────
# STEP 1: KERNEL bzImage
# ─────────────────────────────────────────────
Write-Step "STEP 1/4 -- Copying custom WSL2 binder kernel (bzImage)..."
if (Test-Path $KernelBzImage) {
    Copy-Item $KernelBzImage "$OutputDir\kernel\bzImage" -Force
    $kSize = (Get-Item "$OutputDir\kernel\bzImage").Length
    Write-Ok "bzImage copied ($(Format-Bytes $kSize))"
} else {
    Write-Warn "bzImage not found at $KernelBzImage"
    Write-Warn "Copying build scripts so you can rebuild on the new device."
    Copy-Item "$ProjectRoot\ytuploader\kernel_builder" "$OutputDir\kernel\kernel_builder" -Recurse -Force
    Write-Ok "kernel_builder scripts copied -- run build_wsl_kernel.sh on new device."
}

# ─────────────────────────────────────────────
# STEP 2: .wslconfig
# ─────────────────────────────────────────────
Write-Step "STEP 2/4 -- Copying .wslconfig..."
if (Test-Path $WslConfig) {
    Copy-Item $WslConfig "$OutputDir\kernel\.wslconfig" -Force
    Write-Ok ".wslconfig copied"
} else {
    @"
[wsl2]
kernel=C:\\Users\\%USERNAME%\\wsl-kernel\\bzImage
vmIdleTimeout=-1
"@ | Set-Content "$OutputDir\kernel\.wslconfig"
    Write-Warn ".wslconfig not found -- generated a template."
}

# ─────────────────────────────────────────────
# STEP 3: DOCKER VOLUMES (via WSL)
# ─────────────────────────────────────────────
Write-Step "STEP 3/4 -- Exporting Redroid Docker volumes from WSL..."

Write-Host "    Checking Docker inside WSL..." -ForegroundColor DarkGray
$dockerOk = (Invoke-Wsl "docker info > /dev/null 2>&1 && echo OK").Trim()
if ($dockerOk -ne "OK") {
    Write-Host "    Starting Docker daemon inside WSL..." -ForegroundColor DarkGray
    Invoke-Wsl "systemctl start docker > /dev/null 2>&1 || service docker start > /dev/null 2>&1; sleep 3" | Out-Null
    $dockerOk = (Invoke-Wsl "docker info > /dev/null 2>&1 && echo OK").Trim()
    if ($dockerOk -ne "OK") {
        Write-Fail "Docker is not running inside WSL. Start it and re-run this script."
        exit 1
    }
}
Write-Host "    Docker is running." -ForegroundColor DarkGray

# Stage exports through /tmp inside WSL (no spaces in path = no Docker mount issues)
# Then copy each .tar.gz to the Windows output folder via /mnt/c/...
$wslTmpDir = "/tmp/redroid_vol_export"
Invoke-Wsl "rm -rf $wslTmpDir && mkdir -p $wslTmpDir" | Out-Null

# Build Windows -> WSL path for final copy destination (no spaces issue -- we copy file-by-file)
$driveLetter  = ($OutputDir -replace ":.*","").ToLower()
$pathRest     = ($OutputDir -replace "^[A-Za-z]:\\","") -replace "\\","/"
$wslOutputDir = "/mnt/$driveLetter/$pathRest"
Invoke-Wsl "mkdir -p '$wslOutputDir/volumes'" | Out-Null

$exportedCount = 0
foreach ($vol in $Volumes) {
    Write-Host "    Exporting: $vol ..." -ForegroundColor DarkGray
    $volExists = (Invoke-Wsl "docker volume ls -q --filter name=^${vol}$").Trim()
    if ([string]::IsNullOrWhiteSpace($volExists)) {
        Write-Warn "Volume '$vol' not found -- skipping."
        continue
    }

    # Export to /tmp (no spaces, safe for Docker bind mount)
    $tmpTar = "$wslTmpDir/${vol}.tar.gz"
    Invoke-Wsl "docker run --rm -v ${vol}:/data -v ${wslTmpDir}:/backup alpine sh -c 'tar czf /backup/${vol}.tar.gz -C /data . 2>/dev/null; echo done'" | Out-Null

    # Copy from /tmp to the Windows output folder
    Invoke-Wsl "cp '$tmpTar' '$wslOutputDir/volumes/${vol}.tar.gz' 2>/dev/null; echo copied" | Out-Null

    $winTar = "$OutputDir\volumes\${vol}.tar.gz"
    if (Test-Path $winTar) {
        $vSize = (Get-Item $winTar).Length
        Write-Ok "$vol  ($(Format-Bytes $vSize))"
        $exportedCount++
    } else {
        Write-Warn "Failed to export '$vol' -- check Docker and WSL."
    }
}

# Clean up WSL temp dir
Invoke-Wsl "rm -rf $wslTmpDir" | Out-Null
Write-Host "    Exported $exportedCount / $($Volumes.Count) volumes." -ForegroundColor DarkGray

# ─────────────────────────────────────────────
# STEP 4: PROJECT CODE
# ─────────────────────────────────────────────
Write-Step "STEP 4/4 -- Copying project code..."
Copy-ProjectDir -Source $ProjectRoot -Dest "$OutputDir\code"
Write-Ok "Project code copied (excluded: __pycache__, .git, node_modules, large zips)"

# ─────────────────────────────────────────────
# GENERATE RESTORE SCRIPT (embedded in bundle)
# ─────────────────────────────────────────────
Write-Step "Generating restore_on_new_device.ps1..."

$restoreScriptContent = @'
<#
.SYNOPSIS
    Restores the Redroid + Instagram Uploader system on a new device.
.DESCRIPTION
    Run this on the NEW device after extracting the migration ZIP.
    Automatically:
      1. Installs the custom WSL2 binder kernel
      2. Deploys .wslconfig and restarts WSL
      3. Restores all Redroid Docker volumes
      4. Copies project code to OneDrive Documents
.USAGE
    Right-click -> Run with PowerShell (as Administrator)
    OR in PowerShell: .\restore_on_new_device.ps1
#>
$ErrorActionPreference = "Stop"
$BundleDir   = $PSScriptRoot
$KernelDir   = "$env:USERPROFILE\wsl-kernel"
$ProjectDest = "$env:USERPROFILE\OneDrive\Documents\Projects\insta uploader"

function Write-Step { param([string]$Msg) Write-Host "`n  >> $Msg" -ForegroundColor Cyan }
function Write-Ok   { param([string]$Msg) Write-Host "     OK  $Msg" -ForegroundColor Green }
function Write-Warn { param([string]$Msg) Write-Host "     WARN $Msg" -ForegroundColor Yellow }
function Invoke-Wsl { param([string]$Bash) $r = wsl.exe -d Ubuntu -u root --exec bash -c $Bash 2>&1; return ($r -join "`n") -replace "`0","" }

Write-Host ""
Write-Host "======================================================"
Write-Host "  REDROID MIGRATION RESTORE" -ForegroundColor Magenta
Write-Host "======================================================"

# STEP 1: Kernel
Write-Step "STEP 1/4 -- Installing custom WSL2 binder kernel..."
$null = New-Item -ItemType Directory -Force -Path $KernelDir
if (Test-Path "$BundleDir\kernel\bzImage") {
    Copy-Item "$BundleDir\kernel\bzImage" "$KernelDir\bzImage" -Force
    Write-Ok "bzImage installed at $KernelDir\bzImage"
} elseif (Test-Path "$BundleDir\kernel\kernel_builder\build_wsl_kernel.sh") {
    Write-Warn "No pre-built bzImage. Building kernel now (~20-30 min)..."
    $driveLetter = ($BundleDir -replace ":.*","").ToLower()
    $pathRest    = ($BundleDir -replace "^[A-Za-z]:\\","") -replace "\\","/"
    $wslSrc      = "/mnt/$driveLetter/$pathRest/kernel/kernel_builder"
    Invoke-Wsl "bash '$wslSrc/build_wsl_kernel.sh'"
    Write-Ok "Kernel built and installed."
} else {
    Write-Warn "No kernel found. Rebuild manually with kernel_builder scripts."
}

# STEP 2: .wslconfig
Write-Step "STEP 2/4 -- Deploying .wslconfig..."
$wslCfgSrc = "$BundleDir\kernel\.wslconfig"
if (Test-Path $wslCfgSrc) {
    $content = (Get-Content $wslCfgSrc -Raw) -replace "%USERNAME%", $env:USERNAME
    $content | Set-Content "$env:USERPROFILE\.wslconfig" -Encoding UTF8
    Write-Ok ".wslconfig deployed to $env:USERPROFILE\.wslconfig"
}
Write-Host "    Restarting WSL to load binder kernel..." -ForegroundColor DarkGray
wsl.exe --shutdown | Out-Null
Start-Sleep -Seconds 4
wsl.exe -d Ubuntu -u root --exec bash -c "echo 'WSL reloaded'" | Out-Null

# Verify binder
$binderOk = (Invoke-Wsl "[ -e /dev/binder ] && echo YES || echo NO").Trim()
if ($binderOk -eq "YES") {
    Write-Ok "/dev/binder is PRESENT -- kernel binders are working!"
} else {
    Write-Warn "/dev/binder not found. Check that .wslconfig is correct and WSL restarted."
}

# STEP 3: Docker volumes
Write-Step "STEP 3/4 -- Restoring Redroid Docker volumes..."
$dockerOk = (Invoke-Wsl "docker info > /dev/null 2>&1 && echo OK").Trim()
if ($dockerOk -ne "OK") {
    Invoke-Wsl "systemctl start docker > /dev/null 2>&1 || service docker start > /dev/null 2>&1; sleep 3" | Out-Null
}

$driveLetter = ($BundleDir -replace ":.*","").ToLower()
$pathRest    = ($BundleDir -replace "^[A-Za-z]:\\","") -replace "\\","/"
$wslVolDir   = "/mnt/$driveLetter/$pathRest/volumes"

$tarFiles = Get-ChildItem "$BundleDir\volumes" -Filter "*.tar.gz" -ErrorAction SilentlyContinue
foreach ($tar in $tarFiles) {
    $volName = ($tar.BaseName -replace "\.tar$","")
    Write-Host "    Restoring $volName ..." -ForegroundColor DarkGray
    Invoke-Wsl "docker volume create $volName > /dev/null 2>&1" | Out-Null
    Invoke-Wsl "docker run --rm -v ${volName}:/data -v '$wslVolDir':/backup alpine sh -c 'cd /data && tar xzf /backup/${volName}.tar.gz'" | Out-Null
    Write-Ok "$volName restored"
}

# STEP 4: Project code
Write-Step "STEP 4/4 -- Restoring project code..."
$null = New-Item -ItemType Directory -Force -Path $ProjectDest
Copy-Item "$BundleDir\code\*" $ProjectDest -Recurse -Force
Write-Ok "Project code restored to $ProjectDest"

# Re-init brands DB
Write-Host "    Re-initializing brands database..." -ForegroundColor DarkGray
$dbScript = "$ProjectDest\cli uploader\db.py"
if (Test-Path $dbScript) {
    python $dbScript init 2>&1 | Out-Null
    Write-Ok "brands.db initialized"
}

# Final summary
Write-Host ""
Write-Host "======================================================"
Write-Host "  RESTORE COMPLETE!" -ForegroundColor Green
Write-Host "======================================================"
Write-Host "  Next steps:" -ForegroundColor Green
Write-Host "   1. cd to project root" -ForegroundColor Green
Write-Host "   2. pip install -r requirements.txt  (each service)" -ForegroundColor Green
Write-Host "   3. python run_all.py" -ForegroundColor Green
Write-Host "   4. Open http://localhost:8000" -ForegroundColor Green
Write-Host ""
'@

$restoreScriptContent | Set-Content "$OutputDir\restore_on_new_device.ps1" -Encoding UTF8
Write-Ok "restore_on_new_device.ps1 generated"

# ─────────────────────────────────────────────
# README inside bundle
# ─────────────────────────────────────────────
@"
# Redroid Migration Bundle
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm")

## Contents
  kernel/bzImage          - Custom WSL2 kernel with Android Binder support
  kernel/.wslconfig       - WSL2 config (loads the custom kernel)
  volumes/*.tar.gz        - Redroid Docker volumes (per-brand Android data)
  code/                   - Full project source (insta uploader + CLI uploader + ytuploader)
  restore_on_new_device.ps1 - ONE-CLICK restore script

## How to restore on new device
  1. Extract this ZIP
  2. Right-click restore_on_new_device.ps1 -> Run with PowerShell (as Admin)
  3. Done. Run: python run_all.py

## Volumes included
$(($Volumes | ForEach-Object { "  - $_" }) -join "`n")
"@ | Set-Content "$OutputDir\README.txt" -Encoding UTF8

# ─────────────────────────────────────────────
# ZIP EVERYTHING
# ─────────────────────────────────────────────
Write-Step "Zipping bundle => $OutputZip ..."
Write-Host "    (May take a few minutes depending on volume sizes...)" -ForegroundColor DarkGray

if (Test-Path $OutputZip) { Remove-Item $OutputZip -Force }
Compress-Archive -Path "$OutputDir\*" -DestinationPath $OutputZip -CompressionLevel Optimal

$zipSize = (Get-Item $OutputZip).Length
Write-Ok "ZIP created: $OutputZip  ($([math]::Round($zipSize / 1GB, 2)) GB)"

# ─────────────────────────────────────────────
# DONE
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "======================================================"
Write-Host "  BUNDLE COMPLETE!" -ForegroundColor Green
Write-Host "======================================================"
Write-Host "  Folder : $OutputDir"       -ForegroundColor Green
Write-Host "  ZIP    : $OutputZip"       -ForegroundColor Green
Write-Host ""
Write-Host "  On new device:"            -ForegroundColor Cyan
Write-Host "   1. Extract the ZIP"       -ForegroundColor Cyan
Write-Host "   2. Run restore_on_new_device.ps1 as Admin"  -ForegroundColor Cyan
Write-Host "   3. python run_all.py"     -ForegroundColor Cyan
Write-Host ""

explorer.exe "$env:USERPROFILE\Desktop"
