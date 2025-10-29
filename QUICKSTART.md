# Quick Start - Get Running in 15 Minutes

This is the fastest path to get your CUSD Email Summarizer working.

## Prerequisites Check (2 minutes)

- [ ] Windows 10/11
- [ ] Python 3.9+ installed (`python --version`)
- [ ] Gmail account with school emails
- [ ] 15 minutes of time

## 5-Step Setup

### 1. Install Dependencies (2 min)

```powershell
cd path\to\cusd_summarizer
pip install -r requirements.txt
```

Wait for installation to complete.

### 2. Get Anthropic API Key (3 min)

1. Go to https://console.anthropic.com/
2. Sign up / Log in
3. Go to "API Keys"
4. Create new key
5. Copy the key (starts with `sk-ant-`)

**Set environment variable:**
```powershell
[System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'your-key-here', 'User')
```

Close and reopen PowerShell to apply.

### 3. Set Up Gmail API (5 min)

1. Go to https://console.cloud.google.com/
2. Create new project: "CUSD Summarizer"
3. Enable Gmail API
4. Create OAuth credentials (Desktop app)
5. Download JSON
6. Save as `config\credentials.json`

### 4. Configure (2 min)

Edit `config\config.json`:

```json
{
  "email": {
    "recipient": "YOUR-EMAIL@gmail.com"  ← Change this!
  }
}
```

Create Gmail label "CUSD" and label some recent school emails.

### 5. First Run (3 min)

```powershell
# Validate setup
python setup_check.py

# First run - browser will open for Gmail auth
python main.py
```

Click "Allow" in browser, then check:
- ✅ Console shows "Run completed"
- ✅ File appears in `output/` folder
- ✅ Email in your inbox

## Done! 🎉

Your first digest should be generated.

## Set Up Automation (Optional, +5 min)

1. Open Task Scheduler
2. Create Basic Task: "CUSD Email Digest"
3. Trigger: Daily at 7:00 AM
4. Action: Start a program
   - Program: `C:\Path\To\Python\python.exe`
   - Arguments: `C:\Path\To\cusd_summarizer\main.py`
   - Start in: `C:\Path\To\cusd_summarizer`
5. Settings:
   - Run whether user logged on or not
   - Wake computer to run

## Troubleshooting

### "Environment variable not set"
```powershell
echo $env:ANTHROPIC_API_KEY
```
If empty, rerun Step 2 and restart PowerShell.

### "Credentials not found"
Verify `config\credentials.json` exists.

### "Label CUSD not found"
Create the label in Gmail and label some emails.

### Still stuck?
See SETUP_GUIDE.md for detailed instructions.

## Next Steps

- Review the generated digest
- Adjust config if needed
- Let it run automatically each morning
- Enjoy never missing school events again!

---

**Need more detail?** → See SETUP_GUIDE.md  
**Want to understand how it works?** → See PROJECT_SUMMARY.md  
**Having problems?** → See README.md troubleshooting section
