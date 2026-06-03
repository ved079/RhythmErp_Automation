#!/usr/bin/env powershell
# ============================================================
# COPY V2 FILES — Drop this in your Pacs_Automation root
# Replaces the 7 data files + batch_create scripts with FK-ID-hardcoded versions
# Also adds common/fk_resolver.py and helper scripts
# ============================================================

$SRC = ".\common_settings_v2"
$DST = "."

# ── common/fk_resolver.py ─────────────────────────────────
New-Item -ItemType Directory -Force -Path "$DST\common" | Out-Null
Copy-Item "$SRC\common\fk_resolver.py" "$DST\common\fk_resolver.py" -Force
Write-Host "  [1] common/fk_resolver.py" -ForegroundColor Green

# ── 7 data files (with real FK IDs hardcoded) ─────────────
$modules = @(
    "error_code_mst",
    "hsn_sac",
    "tax_authority",
    "vehicle_master",
    "bank",
    "tax_rate",
    "uom_conversion"
)

$i = 2
foreach ($mod in $modules) {
    $dataDir = "$DST\pages\common_settings\modules\$mod\data"
    $scriptsDir = "$DST\pages\common_settings\modules\$mod\scripts"
    New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
    New-Item -ItemType Directory -Force -Path $scriptsDir | Out-Null

    $dataFile = "$SRC\pages\common_settings\modules\$mod\data\${mod}_data.py"
    $scriptFile = "$SRC\pages\common_settings\modules\$mod\scripts\batch_create.py"

    if (Test-Path $dataFile) {
        Copy-Item $dataFile "$dataDir\${mod}_data.py" -Force
        Write-Host "  [$i] pages/common_settings/modules/$mod/data/${mod}_data.py" -ForegroundColor Green
    }
    $i++

    if (Test-Path $scriptFile) {
        Copy-Item $scriptFile "$scriptsDir\batch_create.py" -Force
        Write-Host "  [$i] pages/common_settings/modules/$mod/scripts/batch_create.py" -ForegroundColor Green
    }
    $i++
}

# ── Helper scripts ────────────────────────────────────────
$scriptsDir = "$DST\pages\common_settings\scripts"
New-Item -ItemType Directory -Force -Path $scriptsDir | Out-Null

Copy-Item "$SRC\pages\common_settings\scripts\fk_discovery.py" "$scriptsDir\fk_discovery.py" -Force
Write-Host "  [$i] pages/common_settings/scripts/fk_discovery.py" -ForegroundColor Green
$i++

Copy-Item "$SRC\pages\common_settings\scripts\run_all_7.py" "$scriptsDir\run_all_7.py" -Force
Write-Host "  [$i] pages/common_settings/scripts/run_all_7.py" -ForegroundColor Green

Write-Host ""
Write-Host "  Done! All v2 files copied." -ForegroundColor Cyan
Write-Host "  Next: git add . && git commit -m 'v2: hardcoded FK IDs for 7 common settings modules'" -ForegroundColor Yellow
