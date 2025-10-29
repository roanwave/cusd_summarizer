# Quick Start: Multi-Profile Email Summarizer

## Overview

Your email summarizer now supports multiple profiles (CUSD and HOA) with a single codebase. Each profile has:
- Separate Gmail labels and settings
- Custom AI prompts tailored to the context
- Profile-specific document sections
- Independent databases and output folders

## Installation

```bash
# Install new dependencies
pip install -r requirements.txt

# This will install:
# - pypdf (for PDF processing)
# - Pillow (for image filtering)
```

## Gmail Setup

### Create HOA Label
1. Open Gmail
2. Create a new label called "HOA"
3. Set up filters to auto-label HOA emails

### Verify CUSD Label
- Ensure your existing "CUSD" label still exists
- No changes needed to CUSD setup

## Usage

### Running CUSD Profile (Default)
```bash
# Use default profile (CUSD)
python main.py

# Or explicitly specify CUSD
python main.py --profile cusd

# Force reprocess all CUSD emails
python main.py --profile cusd --force
```

### Running HOA Profile
```bash
# Process HOA emails
python main.py --profile hoa

# Force reprocess all HOA emails
python main.py --profile hoa --force

# Show HOA statistics
python main.py --profile hoa --stats
```

## What's Different Per Profile?

### CUSD Profile
- **Gmail Label**: "CUSD"
- **Focus**: Kindergarten + school-wide events
- **Image Processing**: Basic (filters out small logos)
- **PDF Processing**: Disabled (school emails are usually text-only)
- **Sections**: Executive Summary, Events, Action Items, Announcements
- **Output**: `output/cusd/CUSD_Digest_[date].docx`
- **Database**: `data/cusd_emails.db`

### HOA Profile
- **Gmail Label**: "HOA"
- **Focus**: Compliance, financials, maintenance, community events
- **Image Processing**: Enhanced (event flyers, violation photos, charts)
- **PDF Processing**: Enabled (newsletters, financials, meeting minutes)
- **Sections**: Executive Summary, Compliance, Financial, Events, Maintenance, Actions, Announcements
- **Output**: `output/hoa/HOA_Digest_[date].docx`
- **Database**: `data/hoa_emails.db`

## New Features

### 1. Image Filtering (Both Profiles)
- Automatically filters out images smaller than 150x150px
- Removes email signatures, logos, and decorative graphics
- Keeps meaningful images: flyers, charts, photos, maps

### 2. PDF Processing (HOA Only)
- Downloads PDF attachments from emails
- Extracts text content (up to 10,000 characters)
- Includes PDF content in AI analysis
- Example PDFs: newsletters, budget reports, meeting minutes

### 3. Profile-Specific AI Prompts
- **CUSD**: Focuses on extracting school events, parent action items
- **HOA**: Focuses on compliance issues, financial notices, maintenance schedules

## File Structure

```
cusd_summarizer/
├── profiles/
│   ├── cusd.json          # CUSD configuration
│   └── hoa.json           # HOA configuration
├── output/
│   ├── cusd/              # CUSD digests
│   └── hoa/               # HOA digests
├── data/
│   ├── cusd_emails.db     # CUSD tracking database
│   └── hoa_emails.db      # HOA tracking database
├── logs/
│   ├── cusd_summarizer.log
│   └── hoa_summarizer.log
└── config/
    ├── config.json        # Base configuration
    ├── credentials.json   # Gmail OAuth (shared)
    └── token.pickle       # Gmail token (shared)
```

## Customizing Profiles

### Editing Prompts
Want to change how AI analyzes emails? Edit the profile JSON:

```json
// profiles/hoa.json
{
  "prompts": {
    "email_system": "Your custom system prompt here...",
    "email_user_template": "Email from: {sender}..."
  }
}
```

### Adding New Sections
To add a custom section to HOA documents:

```json
// profiles/hoa.json
{
  "document": {
    "sections": [
      {
        "name": "my_custom_section",
        "title": "My Custom Section",
        "type": "bullet_list"
      }
    ]
  }
}
```

## Troubleshooting

### "Profile configuration not found"
**Problem**: `python main.py --profile xyz`
**Solution**: Only `cusd` and `hoa` profiles exist. Create `profiles/xyz.json` if you need a new profile.

### "PDF processing not available"
**Problem**: PDFs aren't being processed
**Solution**: Run `pip install pypdf` or `pip install -r requirements.txt`

### "Image filtering not working"
**Problem**: Small logos still appearing in analysis
**Solution**: Ensure Pillow is installed: `pip install Pillow`

### "Wrong label emails being processed"
**Problem**: CUSD emails showing up in HOA digest
**Solution**: Check Gmail labels. Each email should have only one label (CUSD or HOA).

## Switching Between Profiles

You can run both profiles in sequence:

```bash
# Morning: Process CUSD emails
python main.py --profile cusd

# Evening: Process HOA emails
python main.py --profile hoa
```

Each profile:
- Uses its own database (no conflicts)
- Creates separate output files
- Has independent tracking
- Can be run multiple times per day

## Next Steps

1. **Test CUSD**: Run `python main.py --profile cusd` to verify no regressions
2. **Test HOA**: Run `python main.py --profile hoa` with some HOA emails
3. **Review Outputs**: Check the generated Word documents in `output/cusd/` and `output/hoa/`
4. **Tune Prompts**: Edit profile JSON files to adjust AI behavior
5. **Schedule**: Set up Windows Task Scheduler or cron for automatic processing

## Advanced: Creating New Profiles

Want to add a "Work" profile?

1. **Create** `profiles/work.json` (copy from `cusd.json` or `hoa.json`)
2. **Edit** Gmail label, prompts, sections
3. **Run** `python main.py --profile work`

That's it! The system will automatically:
- Create `data/work_emails.db`
- Create `output/work/` directory
- Use Work-specific prompts and sections

## Questions?

See `MULTI_PROFILE_IMPLEMENTATION.md` for detailed technical documentation.
