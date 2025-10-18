# Git History Cleanup Script
# DANGER: This rewrites Git history - all collaborators must re-clone!

Write-Host "=" -NoNewline -ForegroundColor Red
Write-Host "================================================" -ForegroundColor Red
Write-Host "  WARNING: GIT HISTORY REWRITE" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Red
Write-Host "================================================" -ForegroundColor Red
Write-Host ""
Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "  1. Remove all leaked secrets from Git history" -ForegroundColor Yellow
Write-Host "  2. REWRITE all commits (change commit hashes)" -ForegroundColor Yellow
Write-Host "  3. Force push to remote (destructive)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Before proceeding, you MUST:" -ForegroundColor Red
Write-Host "  [x] Revoke all leaked secrets in Azure Portal" -ForegroundColor Red
Write-Host "  [x] Create backup: git clone . ../VideoQnA-LTW-backup" -ForegroundColor Red
Write-Host "  [x] Notify all collaborators (if any)" -ForegroundColor Red
Write-Host ""

$confirm = Read-Host "Have you completed all the above? (type 'YES' to continue)"
if ($confirm -ne "YES") {
    Write-Host "Aborted. Please complete the checklist first." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Step 1: Check if git-filter-repo is installed..." -ForegroundColor Cyan

# Check if git-filter-repo is installed
try {
    $filterRepoCheck = git filter-repo --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Not installed"
    }
    Write-Host "  git-filter-repo found" -ForegroundColor Green
} catch {
    Write-Host "  git-filter-repo not found. Installing..." -ForegroundColor Yellow

    # Try to install via pip
    try {
        pip install git-filter-repo
        Write-Host "  Installed successfully" -ForegroundColor Green
    } catch {
        Write-Host ""
        Write-Host "ERROR: Cannot install git-filter-repo" -ForegroundColor Red
        Write-Host "Please install manually:" -ForegroundColor Yellow
        Write-Host "  pip install git-filter-repo" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Alternative: Use BFG Repo Cleaner" -ForegroundColor Yellow
        Write-Host "  Download from: https://rtyley.github.io/bfg-repo-cleaner/" -ForegroundColor Cyan
        exit 1
    }
}

Write-Host ""
Write-Host "Step 2: Creating secrets replacement file..." -ForegroundColor Cyan

# Create secrets replacement file
$secretsFile = @"
***REMOVED_OPENAI_KEY_OLD*** mTsNg0AU0JPdrn2JiDJQQJ99BHACYeBjFXJ3w3AAABACOGtOFq==>REDACTED_OPENAI_KEY
***REMOVED_SEARCH_KEY***==>REDACTED_SEARCH_KEY
***REMOVED_CLIENT_SECRET***==>REDACTED_CLIENT_SECRET
"@

$secretsFile | Out-File -FilePath "secrets_to_remove.txt" -Encoding UTF8 -NoNewline
Write-Host "  Created secrets_to_remove.txt" -ForegroundColor Green

Write-Host ""
Write-Host "Step 3: Backing up current state..." -ForegroundColor Cyan
git tag backup-before-cleanup HEAD
Write-Host "  Created tag: backup-before-cleanup" -ForegroundColor Green

Write-Host ""
Write-Host "Step 4: Cleaning Git history (this may take a while)..." -ForegroundColor Cyan

try {
    # Run git filter-repo
    git filter-repo --replace-text secrets_to_remove.txt --force

    Write-Host "  Git history cleaned successfully!" -ForegroundColor Green

} catch {
    Write-Host ""
    Write-Host "ERROR during history cleanup:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "To restore backup:" -ForegroundColor Yellow
    Write-Host "  git reset --hard backup-before-cleanup" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "Step 5: Verifying cleanup..." -ForegroundColor Cyan

# Verify that secrets are gone
$verification = @(
    "***REMOVED_OPENAI_KEY_OLD***",
    "***REMOVED_SEARCH_KEY***",
    "***REMOVED_CLIENT_SECRET***"
)

$foundSecrets = $false
foreach ($secret in $verification) {
    $result = git log --all --full-history -S $secret --oneline 2>&1
    if ($result) {
        Write-Host "  WARNING: Secret still found in history: $($secret.Substring(0,20))..." -ForegroundColor Red
        $foundSecrets = $true
    }
}

if (-not $foundSecrets) {
    Write-Host "  Verification passed - no secrets found in history" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "ERROR: Some secrets still exist in history!" -ForegroundColor Red
    Write-Host "Please review manually or try BFG Repo Cleaner instead." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Step 6: Re-adding remote..." -ForegroundColor Cyan

# git filter-repo removes remotes, need to re-add
$remoteUrl = Read-Host "Enter your GitHub remote URL (e.g., https://github.com/user/repo.git)"
if ($remoteUrl) {
    git remote add origin $remoteUrl
    Write-Host "  Remote 'origin' added" -ForegroundColor Green
} else {
    Write-Host "  Skipped - you'll need to add remote manually" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "  CLEANUP SUCCESSFUL!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review the changes: git log --oneline" -ForegroundColor Cyan
Write-Host "  2. Force push to GitHub: git push --force --all" -ForegroundColor Cyan
Write-Host "  3. Force push tags: git push --force --tags" -ForegroundColor Cyan
Write-Host "  4. Delete secrets_to_remove.txt file" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Red
Write-Host "  All collaborators must delete their local copies" -ForegroundColor Red
Write-Host "  and re-clone the repository!" -ForegroundColor Red
Write-Host ""
Write-Host "To restore if something went wrong:" -ForegroundColor Yellow
Write-Host "  git reset --hard backup-before-cleanup" -ForegroundColor Cyan
Write-Host ""

# Cleanup
Write-Host "Do you want to delete the secrets_to_remove.txt file? (Y/N)" -ForegroundColor Yellow
$cleanup = Read-Host
if ($cleanup -eq "Y" -or $cleanup -eq "y") {
    Remove-Item secrets_to_remove.txt -Force
    Write-Host "  Deleted secrets_to_remove.txt" -ForegroundColor Green
}
