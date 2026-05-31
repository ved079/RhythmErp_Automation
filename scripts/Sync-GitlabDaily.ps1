# Daily GitLab sync script for Vedant & Gautam
$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " GitLab Daily Sync (vedant + gautam)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Fetch all latest from GitLab
Write-Host "`n[1/4] Fetching latest from GitLab..." -ForegroundColor Yellow
git fetch gitlab

# 2. Sync vedant's working branch (rhythmerp_integration)
Write-Host "`n[2/4] Updating rhythmerp_integration..." -ForegroundColor Yellow
git checkout rhythmerp_integration
git pull --rebase gitlab rhythmerp_integration
Write-Host "rhythmerp_integration is now up to date with GitLab." -ForegroundColor Green

# 3. Sync gautam_Branch (local only – no push)
Write-Host "`n[3/4] Updating local gautam_Branch (read-only mirror)..." -ForegroundColor Yellow
git checkout gautam_Branch
git reset --hard gitlab/gautam_Branch
Write-Host "Local gautam_Branch is now exactly as GitLab/gautam_Branch." -ForegroundColor Green

# 4. Push vedant's branch back to GitLab (in case local is ahead)
Write-Host "`n[4/4] Pushing rhythmerp_integration to GitLab..." -ForegroundColor Yellow
git checkout rhythmerp_integration
git push gitlab rhythmerp_integration

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Daily sync complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan