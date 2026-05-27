<#
.SYNOPSIS
    EOD Sync Script
    Pushes github/rhythmerp_integration to ALL branches across ALL remotes.
    Every branch on every remote becomes identical to your source of truth.

.USAGE
    Normal run  : .\eod_sync.ps1
    Preview only: .\eod_sync.ps1 -DryRun
#>

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

$remotes = [System.Collections.ArrayList]@("github", "github-private")

# ── GITLAB CHECK ───────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   EOD SYNC  --  Source of Truth: github/rhythmerp_integration" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$gitlabAnswer = Read-Host "Are you on the work network? Include gitlab in sync? [y/n]"
if ($gitlabAnswer.Trim().ToLower() -eq "y") {
    $remotes.Add("gitlab") | Out-Null
    Write-Host ">> Gitlab included." -ForegroundColor Green
} else {
    Write-Host ">> Gitlab skipped. Run again on work network to sync it." -ForegroundColor Yellow
}

if ($DryRun) {
    Write-Host ""
    Write-Host "*** DRY RUN MODE -- nothing will actually be pushed ***" -ForegroundColor Magenta
}

# ── FETCH & UPDATE LOCAL SOURCE BRANCH ────────────────────────────────────────

Write-Host ""
Write-Host "-- Step 1: Fetching latest from '$sourceRemote'..." -ForegroundColor Yellow
git fetch $sourceRemote

if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Could not fetch from '$sourceRemote'. Check your internet and try again." -ForegroundColor Red
    exit 1
}

Write-Host "-- Step 2: Switching to '$sourceBranch' and pulling latest..." -ForegroundColor Yellow
git checkout $sourceBranch

if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Could not checkout '$sourceBranch'. Make sure it exists locally." -ForegroundColor Red
    exit 1
}

git pull $sourceRemote $sourceBranch

if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Pull failed. Resolve issues on '$sourceBranch' before syncing." -ForegroundColor Red
    exit 1
}

Write-Host "OK: Local '$sourceBranch' is up to date with '$sourceRemote'." -ForegroundColor Green

# ── PUSH TO ALL BRANCHES ON ALL REMOTES ───────────────────────────────────────

Write-Host ""
Write-Host "-- Step 3: Pushing to all branches on all remotes..." -ForegroundColor Yellow

$failCount = 0
$successCount = 0

foreach ($remote in $remotes) {
    Write-Host ""
    Write-Host "  Remote: $remote" -ForegroundColor Cyan
    Write-Host "  ------------------------------" -ForegroundColor DarkGray

    foreach ($branch in $targetBranches) {

        $trackingRef = "refs/remotes/$remote/$branch"
        git show-ref --verify --quiet $trackingRef 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "    SKIP: $remote/$branch not found on remote." -ForegroundColor DarkGray
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
    Write-Host "EOD Sync complete! All branches match rhythmerp_integration." -ForegroundColor Green
} else {
    Write-Host "Sync finished with $failCount failure(s) and $successCount success(es). Check errors above." -ForegroundColor Yellow
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""