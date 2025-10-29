# CUSD Email Summarizer - Complete Setup Guide

This guide walks you through setting up the CUSD Email Summarizer from scratch on a Windows machine.

## Prerequisites

- Windows 10 or 11
- Administrator access (for installing Python if needed)
- Gmail account with CUSD emails
- Credit card for Anthropic API (free tier available)

## Step 1: Install Python

### Check if Python is Installed

1. Open PowerShell (Win + X → PowerShell)
2. Run: `python --version`

If you see "Python 3.9" or higher, skip to Step 2.

### Install Python

1. Go to https://www.python.org/downloads/
2. Download Python 3.11 or newer
3. Run the installer
4. ✅ **IMPORTANT**: Check "Add Python to PATH"
5. Click "Install Now"
6. Verify: `python --version`

## Step 2: Download the Project

### Option A: Download ZIP
1. Download cusd_summarizer.zip
2. Extract to: `C:\Users\YourName\cusd_summarizer`

### Option B: Clone Repository
```bash
git clone <repository-url>
cd cusd_summarizer
```

## Step 3: Install Dependencies

Open PowerShell in the project directory:

```powershell
cd C:\Users\YourName\cusd_summarizer
pip install -r requirements.txt
```

This installs:
- Google Gmail API client
- Anthropic Claude API client
- python-docx for document generation
- Pillow for image processing

**Wait** for installation to complete (2-3 minutes).

## Step 4: Set Up Gmail API

### 4.1 Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Click "Select a project" → "New Project"
3. Name it: "CUSD Email Summarizer"
4. Click "Create"
5. Wait for project creation

### 4.2 Enable Gmail API

1. In Google Cloud Console, select your project
2. Go to "APIs & Services" → "Library"
3. Search for "Gmail API"
4. Click "Gmail API"
5. Click "Enable"
6. Wait for activation

### 4.3 Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - User Type: External
   - App name: "CUSD Email Summarizer"
   - User support email: your email
   - Developer contact: your email
   - Click "Save and Continue"
   - Scopes: Skip for now
   - Test users: Add your Gmail address
   - Click "Save and Continue"
4. Back to Create OAuth client ID:
   - Application type: "Desktop app"
   - Name: "CUSD Summarizer"
   - Click "Create"
5. Click "Download JSON"
6. Save as `credentials.json`

### 4.4 Install Credentials

1. Move `credentials.json` to: `C:\Users\YourName\cusd_summarizer\config\credentials.json`
2. Verify the file is in the right location

## Step 5: Get Anthropic API Key

### 5.1 Create Anthropic Account

1. Go to https://console.anthropic.com/
2. Sign up with email
3. Verify your email

### 5.2 Get API Key

1. Log in to Anthropic Console
2. Go to "API Keys"
3. Click "Create Key"
4. Name it: "CUSD Summarizer"
5. Copy the key (starts with `sk-ant-`)
6. ⚠️ **IMPORTANT**: Save it securely - you can't see it again!

### 5.3 Set Environment Variable

**PowerShell (Recommended):**
```powershell
[System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'sk-ant-your-key-here', 'User')
```

**Command Prompt:**
```cmd
setx ANTHROPIC_API_KEY "sk-ant-your-key-here"
```

**⚠️ IMPORTANT**: Replace `sk-ant-your-key-here` with your actual key!

### 5.4 Verify

Close and reopen PowerShell, then:
```powershell
echo $env:ANTHROPIC_API_KEY
```

You should see your API key.

## Step 6: Configure the Application

### 6.1 Edit config.json

Open `config\config.json` in a text editor.

Change the recipient email:
```json
{
  "email": {
    "recipient": "your-actual-email@gmail.com",  ← Change this
    "send_digest": true
  }
}
```

Save the file.

### 6.2 Create Gmail Label

1. Open Gmail in browser
2. Click "Create new label" (in sidebar)
3. Name it: `CUSD` (exactly as shown)
4. Click "Create"
5. Label some recent school emails with "CUSD"

## Step 7: Run Setup Check

```powershell
python setup_check.py
```

This checks:
- ✓ Python version
- ✓ Dependencies installed
- ✓ API key set
- ✓ Gmail credentials
- ✓ Config file

If any checks fail, review the relevant step above.

## Step 8: First Run

### 8.1 Authenticate

```powershell
python main.py
```

What happens:
1. Browser opens for Gmail OAuth
2. Select your Gmail account
3. Click "Allow" (trust yourself!)
4. Browser shows "Success" message
5. Close browser
6. Application continues processing

### 8.2 Verify Output

Check for:
- Console output showing emails processed
- New file in `output/` folder: `CUSD_Digest_October_13_2025.docx`
- Email in your inbox: "CUSD Daily Digest - October 13, 2025"

### 8.3 Review Digest

1. Open the Word document
2. Check the summary quality
3. Verify events are correct
4. Ensure action items make sense

## Step 9: Set Up Scheduled Execution

### 9.1 Find Python Path

```powershell
where.exe python
```

Copy the path (e.g., `C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe`)

### 9.2 Create Scheduled Task

1. Open Task Scheduler (Win + R → `taskschd.msc`)
2. Click "Create Basic Task"

**Name and Description:**
- Name: "CUSD Email Digest"
- Description: "Daily school email summarizer"
- Click "Next"

**Trigger:**
- When: "Daily"
- Click "Next"
- Start: Today's date
- Time: "7:00:00 AM"
- Recur every: "1 days"
- Click "Next"

**Action:**
- Action: "Start a program"
- Click "Next"
- Program/script: (Paste Python path from step 9.1)
- Add arguments: `C:\Users\YourName\cusd_summarizer\main.py`
- Start in: `C:\Users\YourName\cusd_summarizer`
- Click "Next"

**Finish:**
- ☑ "Open the Properties dialog"
- Click "Finish"

**Properties (Advanced Settings):**
- General tab:
  - ☑ "Run whether user is logged on or not"
  - ☑ "Run with highest privileges"
- Triggers tab:
  - Edit trigger
  - ☑ "Enabled"
- Settings tab:
  - ☑ "Allow task to be run on demand"
  - ☑ "Run task as soon as possible after a scheduled start is missed"
  - ☑ "If the task fails, restart every": 15 minutes
  - "Attempt to restart up to": 3 times
- Click "OK"
- Enter your Windows password if prompted

### 9.3 Test Scheduled Task

1. In Task Scheduler, find "CUSD Email Digest"
2. Right-click → "Run"
3. Check `logs\cusd_summarizer.log` for execution
4. Verify new digest was created

## Step 10: Verify Everything Works

### Manual Test
```powershell
python main.py --stats
```

Should show:
- Total processed emails
- Recent digests
- No errors

### Check Logs
```powershell
cat logs\cusd_summarizer.log
```

Look for:
- No ERROR messages
- "Run completed" messages
- Successful email processing

### Review Output
Check `output\` folder for digest documents.

## Troubleshooting

### "Module not found" Error

**Solution:**
```powershell
pip install -r requirements.txt --upgrade
```

### "Environment variable not set"

**Solution:**
```powershell
[System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'your-key', 'User')
```

Then restart PowerShell.

### "Credentials file not found"

**Solution:**
- Verify `config\credentials.json` exists
- Re-download from Google Cloud Console if needed

### "Label 'CUSD' not found"

**Solutions:**
1. Create the label in Gmail
2. Label some emails with it
3. Change label name in `config\config.json`

### OAuth Not Working

**Solutions:**
1. Delete `config\token.pickle`
2. Run `python main.py` again
3. Complete OAuth flow in browser

### No Emails Processing

**Checks:**
1. Are there emails labeled "CUSD"?
2. Are they from last 48 hours?
3. Run with --force: `python main.py --force`

### Scheduled Task Not Running

**Checks:**
1. Task Scheduler → CUSD Email Digest → Properties
2. Check "Last Run Result" (should be 0x0)
3. Review History tab
4. Check logs: `logs\cusd_summarizer.log`

## Daily Usage

Once set up, the system runs automatically:

1. **Every morning at 7:00 AM**:
   - Scans Gmail for new CUSD emails
   - Summarizes with AI
   - Generates digest document
   - Emails you the summary

2. **You receive**:
   - Email with digest summary
   - Word document attachment
   - Consolidated event calendar
   - Prioritized action items

3. **Manual runs** (if needed):
   ```powershell
   python main.py
   ```

## Maintenance

### Weekly
- Review digest quality
- Check logs for errors
- Verify API usage at https://console.anthropic.com/

### Monthly
- Old tracking records auto-cleaned (30 days)
- Update dependencies: `pip install -r requirements.txt --upgrade`
- Review API costs

## Getting Help

### Check Logs
```powershell
# View last 50 lines
Get-Content logs\cusd_summarizer.log -Tail 50

# Search for errors
Select-String -Path logs\cusd_summarizer.log -Pattern "ERROR"
```

### Check Stats
```powershell
python main.py --stats
```

### Force Reprocess
```powershell
python main.py --force
```

## Cost Expectations

### Anthropic API
- ~10 emails/day: $5-10/month
- ~20 emails/day: $10-20/month
- First $5-10 often covered by free credits

### Gmail API
- Free within generous quotas
- No credit card required

## Security Notes

### Keep Private
- `config\credentials.json` - Contains OAuth client ID
- `config\token.pickle` - Contains refresh token
- Never share your ANTHROPIC_API_KEY

### Safe to Share
- `config\config.json` (after removing your email)
- All code files
- README and documentation

## Success Checklist

✅ Python 3.9+ installed  
✅ Dependencies installed  
✅ Gmail API enabled  
✅ OAuth credentials created  
✅ Anthropic API key set  
✅ Config file updated  
✅ Gmail label created  
✅ First run successful  
✅ Scheduled task created  
✅ Digest document generated  
✅ Email received  

## Next Steps

Once everything is working:
1. Let it run for a week
2. Review digest quality
3. Adjust config if needed
4. Customize prompts in `modules/ai_summarizer.py`
5. Enjoy automated school email management! 🎉

---

**Need help?** Review the README.md for more details.
