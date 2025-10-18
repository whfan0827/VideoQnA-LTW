# Security Incident Report - 2025-10-18

## Incident Summary

**Severity**: CRITICAL
**Date Discovered**: 2025-10-18
**Date of First Exposure**: 2025-08-27 (commit eb37df5)
**Exposure Duration**: ~2 months
**Repository Visibility**: PUBLIC

## What Was Leaked

The following secrets were hardcoded in PowerShell deployment scripts and committed to public GitHub repository:

### 1. Azure OpenAI API Key
```
Key: ***REMOVED_OPENAI_KEY_OLD*** mTsNg0AU0JPdrn2JiDJQQJ99BHACYeBjFXJ3w3AAABACOGtOFq
Location: Azure Portal → Azure OpenAI → Keys and Endpoint
Action Required: Regenerate key immediately
```

### 2. Azure AI Search Admin Key
```
Key: ***REMOVED_SEARCH_KEY***
Location: Azure Portal → Azure AI Search → Keys
Action Required: Regenerate key immediately
```

### 3. Azure Service Principal Client Secret
```
Secret: ***REMOVED_CLIENT_SECRET***
Location: Azure Portal → Azure Active Directory → App registrations → Certificates & secrets
Action Required: Delete and create new secret
```

## Affected Files (Now Deleted)

- `deploy-terraform.ps1`
- `update-container-app.ps1`
- `update-containerapp-powershell.ps1`
- `update-containerapp-azpowershell.ps1`

## Immediate Actions Taken

- [x] Deleted all files containing hardcoded secrets
- [ ] **PENDING**: Revoke all leaked secrets in Azure Portal
- [ ] **PENDING**: Clean Git history to remove secrets from all commits
- [ ] **PENDING**: Force push cleaned history to GitHub

## Required Actions (DO THIS NOW!)

### Step 1: Revoke All Secrets (15 minutes)

#### A. Azure OpenAI API Key
1. Go to https://portal.azure.com
2. Navigate to your Azure OpenAI resource
3. Go to "Keys and Endpoint"
4. Click "Regenerate" for both Key 1 and Key 2
5. Save new keys to password manager
6. Update your local `.env` file

#### B. Azure AI Search Admin Key
1. Go to https://portal.azure.com
2. Navigate to your Azure AI Search resource
3. Go to "Keys" under Settings
4. Click "Regenerate primary key"
5. Save new key to password manager
6. Update your local `.env` file

#### C. Azure Service Principal Secret
1. Go to https://portal.azure.com
2. Navigate to Azure Active Directory → App registrations
3. Find your application
4. Go to "Certificates & secrets"
5. Delete the leaked secret (***REMOVED_CLIENT_SECRET***)
6. Create new secret
7. Save to password manager
8. Update your local `.env` file

### Step 2: Check Azure Activity Logs

Check for suspicious activity:
```
Azure Portal → Activity Log → Filter by:
- Time range: Last 60 days
- Resource type: All
- Look for unexpected operations
```

If you find suspicious activity, consider:
- Checking billing for unexpected charges
- Reviewing all resource configurations
- Changing all related credentials

### Step 3: Clean Git History

You MUST clean Git history because:
- This is a PUBLIC repository
- Secrets are in commit history (visible to anyone)
- Deleting files is NOT enough

Choose one method:

#### Option A: Using git-filter-repo (Recommended)

```powershell
# Install git-filter-repo
pip install git-filter-repo

# Create secrets file
@"
***REMOVED_OPENAI_KEY_OLD*** mTsNg0AU0JPdrn2JiDJQQJ99BHACYeBjFXJ3w3AAABACOGtOFq==>REDACTED_OPENAI_KEY
***REMOVED_SEARCH_KEY***==>REDACTED_SEARCH_KEY
***REMOVED_CLIENT_SECRET***==>REDACTED_CLIENT_SECRET
"@ | Out-File -FilePath secrets.txt -Encoding UTF8

# Clean history
git filter-repo --replace-text secrets.txt

# Force push (DESTRUCTIVE - rewrites history)
git push --force --all
git push --force --tags
```

#### Option B: Using BFG Repo Cleaner (Faster)

```powershell
# Download BFG from https://rtyley.github.io/bfg-repo-cleaner/
# Then run:

java -jar bfg.jar --replace-text secrets.txt
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force --all
git push --force --tags
```

### Step 4: Verify Cleanup

```powershell
# Search for any remaining secrets
git log --all --full-history -S "***REMOVED_CLIENT_SECRET***"
# Should return nothing

git log --all --full-history -S "***REMOVED_OPENAI_KEY_OLD***"
# Should return nothing
```

## Prevention Measures Implemented

### 1. Pre-commit Hook

Created `.git/hooks/pre-commit` to prevent future leaks:

```bash
#!/bin/sh
# Prevent committing secrets

if git diff --cached --diff-filter=ACM | grep -E "(['\"])([A-Za-z0-9~_-]{32,})\1"; then
    echo "=========================================="
    echo "ERROR: Detected potential secret in commit"
    echo "=========================================="
    echo "Please remove secrets and use environment variables instead."
    exit 1
fi

if git diff --cached --diff-filter=ACM | grep -E "(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]+['\"]"; then
    echo "=========================================="
    echo "ERROR: Detected hardcoded credentials"
    echo "=========================================="
    exit 1
fi
```

### 2. GitLeaks Configuration

Created `.gitleaks.toml` for automated scanning.

### 3. Updated .gitignore

Ensured all sensitive files are excluded.

## Lessons Learned

1. **Never use default parameter values for secrets** - Even in "test" scripts
2. **Always use environment variables** - Never hardcode credentials
3. **Implement pre-commit hooks** - Prevent accidents before they happen
4. **Regular secret rotation** - Don't wait for incidents
5. **Audit before making repo public** - Scan for secrets first

## Timeline

- **2025-08-27**: Secrets first committed (commit eb37df5)
- **2025-08-30**: Additional commits with same secrets (commit 31f7dba)
- **2025-10-18**: Incident discovered and remediated

## Post-Incident Checklist

- [ ] All 3 secrets revoked in Azure Portal
- [ ] New secrets generated and saved securely
- [ ] Local `.env` updated with new secrets
- [ ] Azure activity logs reviewed for suspicious activity
- [ ] Git history cleaned and force-pushed
- [ ] Pre-commit hooks installed
- [ ] All team members notified (if applicable)
- [ ] Billing reviewed for unexpected charges
- [ ] This incident documented

## Contact

If you discover any security issues, please:
1. Do NOT create a public GitHub issue
2. Contact the repository owner directly
3. Report to security@[your-domain] if available

---

**Status**: ACTIVE INCIDENT - Secrets revocation pending
**Next Review**: After all checklist items completed
