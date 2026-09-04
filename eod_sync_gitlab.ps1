#
# .SYNOPSIS
#     EOD Sync — GitLab only
#     Pushes rhythmerp_integration to all branches on gitlab.
#     Run this when on the work network.
#
# .USAGE
#     Normal run  : .\eod_sync_gitlab.ps1
#     Preview only: .\eod_sync_gitlab.ps1 -DryRun
#

param(
    [switch]$DryRun
)

# ── CONFIG ─────────────────────────────────────────────────────────────────────

$sourceRemote = "github"
$sourceBranch = "rhythmerp_integration"

$targetBranches = @(
    "main",
    "rhythmerp_integration",
    "gautam_Branch",
    "bhagyesh_Branch",
    "vedant_backup_branch"
)

$remotes = @("gitlab")

# ── HEADER ─────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   EOD SYNC (GitLab)  --  Source: github/rhythmerp_integration" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Make sure you are on the work network before continuing." -ForegroundColor Yellow
Write-Host ""

if ($DryRun) {
    Write-Host "*** DRY RUN MODE -- nothing will actually be pushed ***" -ForegroundColor Magenta
    Write-Host ""
}

# ── FETCH & UPDATE LOCAL SOURCE BRANCH ────────────────────────────────────────

Write-Host "-- Step 1: Fetching latest from '$sourceRemote'..." -ForegroundColor Yellow
git fetch $sourceRemote
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: Could not fetch from '$sourceRemote'." -ForegroundColor Red; exit 1 }

Write-Host "-- Step 2: Switching to '$sourceBranch' and pulling latest..." -ForegroundColor Yellow
git checkout $sourceBranch
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: Could not checkout '$sourceBranch'." -ForegroundColor Red; exit 1 }

git pull $sourceRemote $sourceBranch
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: Pull failed. Resolve issues before syncing." -ForegroundColor Red; exit 1 }

Write-Host "OK: Local '$sourceBranch' is up to date with '$sourceRemote'." -ForegroundColor Green

# ── PUSH TO GITLAB ─────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "-- Step 3: Pushing to all branches on GitLab..." -ForegroundColor Yellow

$failCount    = 0
$successCount = 0
$skipCount    = 0

foreach ($remote in $remotes) {
    Write-Host ""
    Write-Host "  Remote: $remote" -ForegroundColor Cyan
    Write-Host "  ------------------------------" -ForegroundColor DarkGray
    Write-Host "    (refreshing $remote refs...)" -ForegroundColor DarkGray
    git fetch $remote --quiet 2>$null

    foreach ($branch in $targetBranches) {
        $trackingRef = "refs/remotes/$remote/$branch"
        git show-ref --verify --quiet $trackingRef 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "    SKIP: $remote/$branch not found on remote." -ForegroundColor DarkGray
            $skipCount++
            continue
        }

        if ($DryRun) {
            Write-Host "    [DryRun] Would push $sourceBranch --> $remote/$branch" -ForegroundColor Magenta
        } else {
            Write-Host "    Pushing --> $remote/$branch ..." -ForegroundColor Yellow
            git push $remote "${sourceBranch}:${branch}" --force
            if ($LASTEXITCODE -eq 0) {
                Write-Host "    DONE: $remote/$branch synced." -ForegroundColor Green
                $successCount++
            } else {
                Write-Host "    FAILED: $remote/$branch could not be pushed." -ForegroundColor Red
                $failCount++
            }
        }
    }
}

# ── SUMMARY ────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "Dry run done. Run without -DryRun to actually sync." -ForegroundColor Magenta
} elseif ($failCount -eq 0) {
    Write-Host "EOD Sync (GitLab) complete!  Pushed: $successCount  Skipped: $skipCount  Failed: 0" -ForegroundColor Green
    Write-Host "All branches match rhythmerp_integration." -ForegroundColor Green
} else {
    Write-Host "Sync finished. Pushed: $successCount  Skipped: $skipCount  Failed: $failCount" -ForegroundColor Yellow
    Write-Host "Check the errors above." -ForegroundColor Yellow
}
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
