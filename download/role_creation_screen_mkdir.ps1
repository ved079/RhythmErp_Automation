# Role Creation Screen — Folder Structure & PowerShell mkdir Script
# ============================================================
# Run this script from the PROJECT ROOT to create all directories.
# Then copy the 4 Python files into their respective locations.

# Folder Tree:
# ------------
# project_root/
# ├── pages/
# │   └── access/
# │       └── modules/
# │           └── role_creation_screen/
# │               ├── __init__.py
# │               ├── role_creation_page.py          ← Page Object
# │               ├── data/
# │               │   ├── __init__.py
# │               │   └── role_creation_data.py      ← Data generators
# │               └── test/
# │                   ├── __init__.py
# │                   ├── conftest.py                ← Fixtures + hooks
# │                   └── test_role_creation_screen_validation.py  ← 45 tests
# ├── common/
# │   ├── base_page.py         (existing)
# │   ├── browser_utils.py     (existing)
# │   └── logger.py            (existing)
# ├── config.py                (existing)
# └── reports/
#     └── (auto-generated)

# PowerShell mkdir script:
# ------------------------

$dirs = @(
    "pages\access\modules\role_creation_screen",
    "pages\access\modules\role_creation_screen\data",
    "pages\access\modules\role_creation_screen\test",
    "reports"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "Exists:  $dir" -ForegroundColor Yellow
    }
}

# Create __init__.py files
$initFiles = @(
    "pages\access\modules\role_creation_screen\__init__.py",
    "pages\access\modules\role_creation_screen\data\__init__.py",
    "pages\access\modules\role_creation_screen\test\__init__.py"
)

foreach ($file in $initFiles) {
    if (-not (Test-Path $file)) {
        Set-Content -Path $file -Value ""
        Write-Host "Created: $file" -ForegroundColor Cyan
    } else {
        Write-Host "Exists:  $file" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Folder structure created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Copy role_creation_page.py            -> pages\access\modules\role_creation_screen\" -ForegroundColor White
Write-Host "  2. Copy role_creation_data.py             -> pages\access\modules\role_creation_screen\data\" -ForegroundColor White
Write-Host "  3. Copy conftest.py                       -> pages\access\modules\role_creation_screen\test\" -ForegroundColor White
Write-Host "  4. Copy test_role_creation_screen_validation.py -> pages\access\modules\role_creation_screen\test\" -ForegroundColor White
Write-Host ""
Write-Host "Run tests with:" -ForegroundColor Cyan
Write-Host "  python -m pytest pages/access/modules/role_creation_screen/test/test_role_creation_screen_validation.py -v --tb=short" -ForegroundColor Cyan
