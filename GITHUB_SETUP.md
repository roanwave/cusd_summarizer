# GitHub Repository Setup Guide

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `cusd-summarizer`
3. Description: "Automated email digest system for school communications using Claude AI"
4. Visibility: Private (recommended) or Public
5. ✅ Add README file (we'll replace it)
6. ✅ Add .gitignore (select Python template)
7. ✅ Choose license: MIT
8. Click "Create repository"

## Step 2: Prepare Local Files

From your `C:\Users\erick\py\cusd_summarizer\` directory:

```powershell
# Copy the GitHub files we created
copy C:\Users\erick\Downloads\README.md .
copy C:\Users\erick\Downloads\ARCHITECTURE.md .
copy C:\Users\erick\Downloads\.gitignore .
copy C:\Users\erick\Downloads\LICENSE .
copy C:\Users\erick\Downloads\requirements.txt .
copy C:\Users\erick\Downloads\config.example.json config\

# Verify your secrets are gitignored
type .gitignore | findstr config
# Should show: config/config.json, config/credentials.json, config/token.pickle
```

## Step 3: Initialize Git

```powershell
cd C:\Users\erick\py\cusd_summarizer

# Initialize git repository
git init

# Add all files (gitignore will protect secrets)
git add .

# Check what will be committed (should NOT include config.json, credentials.json, token.pickle)
git status

# Verify no secrets are staged
git status | findstr config.json
git status | findstr credentials.json
git status | findstr token.pickle
# These should return NOTHING

# Commit
git commit -m "Initial commit: Working CUSD email summarizer v3.4"
```

## Step 4: Push to GitHub

```powershell
# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/cusd-summarizer.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 5: Verify on GitHub

1. Go to `https://github.com/YOUR_USERNAME/cusd-summarizer`
2. Check that README.md displays properly
3. Verify modules/ directory is present
4. **CRITICAL:** Confirm config/config.json is NOT visible
5. **CRITICAL:** Confirm config/credentials.json is NOT visible
6. **CRITICAL:** Confirm data/ directory is NOT visible

## Step 6: Share with Next Claude Session

Use this prompt for the next session:

```
I have a working CUSD email summarizer and want to clone it for HOA emails.

GitHub Repository: https://github.com/YOUR_USERNAME/cusd-summarizer

Please review the repository (especially README.md, ARCHITECTURE.md, and modules/ai_summarizer.py) 
to understand the system, then help me:

1. Clone it for HOA emails (different label: "HOA" instead of "CUSD")
2. Adapt prompts for homeowner context (not kindergarten parent)
3. Handle inline images (HOA emails have lots of JPG/PNG/PDF images)
4. Keep both systems maintainable

Key question: Should I create a separate hoa_summarizer/ directory, or make the system 
generic with a config parameter?
```

## Security Checklist

Before pushing, verify these are gitignored:

```powershell
# These commands should return NOTHING if properly gitignored:
git status | findstr "config.json"
git status | findstr "credentials.json"
git status | findstr "token.pickle"
git status | findstr "processed_emails.db"
git status | findstr ".docx"

# If any appear, add to .gitignore and re-commit
```

## Optional: Add Repository Badges

Edit README.md on GitHub and add at the top:

```markdown
# CUSD Email Summarizer

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production-brightgreen.svg)
```

## Future: Cloning for HOA

When ready to create HOA version:

**Option A: Separate Repository**
```powershell
# Clone the CUSD repo
git clone https://github.com/YOUR_USERNAME/cusd-summarizer.git hoa-summarizer
cd hoa-summarizer

# Update remote
git remote set-url origin https://github.com/YOUR_USERNAME/hoa-summarizer.git

# Make HOA-specific changes
# Commit and push
```

**Option B: Monorepo with Multiple Configs**
```powershell
# Keep same repo, add HOA config
cd C:\Users\erick\py\cusd_summarizer
cp config/config.example.json config/hoa_config.json

# Edit hoa_config.json: change label to "HOA", different database path
# Run with: python main.py --config config/hoa_config.json
```

## Troubleshooting

**Error: "Permission denied (publickey)"**
- Use HTTPS instead of SSH: `https://github.com/YOUR_USERNAME/cusd-summarizer.git`
- Or set up SSH keys: https://docs.github.com/en/authentication

**Error: "remote: Repository not found"**
- Verify repository name matches exactly
- Check you're using correct GitHub username

**Accidentally committed secrets:**
```powershell
# Remove from history (nuclear option)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch config/config.json" \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push origin --force --all
```

**Better: Use git-secrets**
```powershell
# Prevent committing secrets
git secrets --install
git secrets --register-aws
git secrets --add 'sk-ant-[a-zA-Z0-9]+'  # Anthropic API keys
```

## Repository Statistics

After setup, you should have:
- ~10-15 files committed
- ~2,000-3,000 lines of code
- 0 secrets exposed
- All documentation included

## Next Steps

1. Push to GitHub
2. Review on GitHub web interface
3. Copy repository URL
4. Use NEXT_SESSION_CONTEXT_WITH_REPO.md prompt in new Claude session
5. Begin HOA implementation
