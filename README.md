# CUSD Email Summarizer

Automated email digest system for Clovis Unified School District communications. Processes Gmail messages, extracts events and action items using Claude AI, and generates professional Word document digests.

## Overview

This system:
1. Fetches emails labeled "CUSD" from Gmail
2. Extracts text content and metadata
3. Uses Claude AI to extract structured data (events, action items, dates)
4. Generates a consolidated Word document digest
5. Tracks processed emails to avoid duplicates

## Features

- ✅ **Automated Event Extraction** - Identifies dates, times, locations, requirements
- ✅ **Professional Word Documents** - Tables, formatting, sections
- ✅ **Smart Deduplication** - SQLite tracking prevents reprocessing
- ✅ **Priority Indicators** - 🔴 HIGH, 🟡 MEDIUM, 🟢 LOW action items
- ✅ **Markdown Cleanup** - Removes formatting artifacts from AI responses
- ✅ **Multi-Event Detection** - Separate entries for each event in multi-day emails

## Architecture

```
Gmail API → Email Processor → AI Summarizer → Document Generator
                ↓                    ↓
           Tracker DB         Claude API (Sonnet 4.5)
```

### Components

- **gmail.py** - Gmail API integration with OAuth 2.0
- **email_processor.py** - Extracts text, HTML, images, attachments
- **ai_summarizer.py** - Claude API for JSON data extraction
- **document_generator.py** - Word document creation with tables
- **tracker.py** - SQLite database for processed email tracking
- **cusd_summarizer.py** - Main orchestrator workflow

## Requirements

```
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1
google-api-python-client>=2.100.0
anthropic>=0.34.0
python-docx>=1.1.0
```

## Configuration

Create `config/config.json`:

```json
{
  "gmail": {
    "credentials_file": "config/credentials.json",
    "token_file": "config/token.pickle",
    "label": "CUSD"
  },
  "anthropic": {
    "api_key": "your-api-key-here",
    "model": "claude-sonnet-4-20250514"
  },
  "processing": {
    "lookback_hours": 72,
    "max_emails": 50,
    "body_char_limit": 8000
  },
  "output": {
    "directory": "output",
    "email_to": "your-email@example.com"
  },
  "database": {
    "path": "data/processed_emails.db"
  }
}
```

## Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials as `config/credentials.json`
6. First run will open browser for OAuth authorization
7. Token saved to `config/token.pickle` for future runs

## Anthropic API Setup

1. Get API key from [Anthropic Console](https://console.anthropic.com/)
2. Add to `config/config.json`

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/cusd-summarizer.git
cd cusd-summarizer

# Install dependencies
pip install -r requirements.txt

# Set up configuration
cp config/config.example.json config/config.json
# Edit config.json with your API keys

# Set up Gmail OAuth (place credentials.json in config/)
# Run for first-time OAuth flow
python main.py
```

## Usage

### Normal Run
Processes new emails since last run:
```bash
python main.py
```

### Force Reprocess
Reprocess all emails with CUSD label:
```bash
python main.py --force
```

### Show Statistics
Display processing statistics:
```bash
python main.py --stats
```

## Output Format

### Word Document Structure

**Executive Summary**
- 3-5 sentence overview of all communications

**Upcoming Events** (Table)
| Event | Date | Time | Location |
|-------|------|------|----------|
| Raven Run | Monday, October 27th | 1:45 PM | School field |
| Pumpkin Patch Trip | Tuesday, October 28th | 7:45-11:45 AM | Off-site |

**Event Details**
Detailed information for each event with:
- Schedule modifications
- Items to bring
- Dress codes
- Costs and permissions
- Source emails

**Action Items**
- 🔴 [HIGH] Return permission slip by Friday
- 🟡 [MEDIUM] Sign up for volunteer shifts
- 🟢 [LOW] Wednesday early release (ELC pickup 5:00 PM)

**Important Announcements**
- Bullet list of school-wide announcements

**Individual Email Summaries**
Full summary of each processed email

## Prompting Strategy (CRITICAL)

The AI prompting went through several iterations. Here's what works:

### ✅ Current Approach (Working)
```python
system_prompt = """You are a JSON data extractor for school emails.

CRITICAL: Your response MUST be ONLY valid JSON. No markdown, no explanations.

Extract: summary, events (array), action_items, importance, key_dates

For multi-day emails, create SEPARATE event objects for EACH day.

JSON schema:
{...}

CRITICAL OUTPUT REQUIREMENT: Return ONLY the JSON object. Just raw JSON starting with {
"""
```

**Key lessons:**
1. **Keep it short** - Long chatty prompts confuse the AI
2. **Crystal clear output format** - "ONLY JSON" repeated 3 times
3. **No conflicting instructions** - Don't say "plain text" when you need JSON
4. **Concrete examples** - Show exactly how to split multi-day events

### ❌ What Failed
- Long prompts with extensive examples
- Instructions about "plain text" and "no markdown" 
- Asking for detailed analysis reports
- Result: AI returned markdown reports instead of JSON

## Troubleshooting

### JSON Parsing Errors
**Symptom:** `ERROR - Error parsing JSON response: Expecting value: line 1 column 1`

**Cause:** AI returning markdown/text instead of JSON

**Fix:** Ensure prompt emphasizes JSON-only output, no conflicting instructions

### Email Content Truncated
**Symptom:** Summaries end mid-sentence with "..."

**Cause:** `body_char_limit` too low or paragraph length limit

**Fix:** 
- Increase `body_char_limit` in config (current: 8000)
- document_generator.py splits long paragraphs automatically

### Events Not Showing in Table
**Symptom:** Events mentioned in summary but not in table

**Cause:** AI not creating separate event objects

**Fix:** Prompt emphasizes "SEPARATE event objects for EACH day"

### Missing Events from Multi-Day Emails
**Symptom:** Only first 2 of 4 events extracted

**Cause:** AI combining events instead of separating

**Fix:** Added explicit example in prompt showing 4 separate events

## Database Schema

```sql
CREATE TABLE processed_emails (
    message_id TEXT PRIMARY KEY,
    subject TEXT,
    sender TEXT,
    received_date TEXT,
    processed_date TEXT,
    summary TEXT,  -- JSON string
    digest_id TEXT
);

CREATE TABLE digests (
    digest_id TEXT PRIMARY KEY,
    created_date TEXT,
    date_range TEXT,
    email_count INTEGER,
    output_path TEXT
);
```

## Token Usage & Costs

### Per Email
- Input: ~1,500-2,500 tokens (8000 char email)
- Output: ~500-1,000 tokens (JSON response)
- Cost: ~$0.01-0.02 per email

### Per Digest Consolidation
- Input: ~5,000-10,000 tokens (multiple summaries)
- Output: ~1,000-2,000 tokens
- Cost: ~$0.05-0.08 per digest

### Monthly Estimates
- Light use (10 emails/day): $10-15/month
- Normal use (20 emails/day): $18-30/month
- Heavy use (50 emails/day): $40-60/month

## Development History

### v1.0 - Initial Implementation
- Basic email fetching and AI summarization
- Simple text output

### v2.0 - Word Document Generation
- Professional document formatting
- Tables and sections

### v3.0 - Prompt Overhaul
- Fixed JSON parsing issues
- Improved event extraction
- Added multi-event detection

### v3.1 - Content Fixes
- Increased character limits (4000 → 8000)
- Fixed email truncation
- Events table with proper columns

### v3.2 - Pre-emptive Fixes
- Explicit NO MARKDOWN instruction
- Increased token limits (3000/4000)
- Table column widths
- Defensive type checking

### v3.3 - Event Extraction
- Separate event per day instruction
- Preservation during consolidation
- End-of-prompt reminders

### v3.4 - Production Ready (Current)
- Ultra-clear JSON-only prompts
- Paragraph splitting for long text
- Comprehensive error logging
- All known issues resolved

## Project Structure

```
cusd_summarizer/
├── main.py                          # Entry point
├── config/
│   ├── config.json                  # Configuration (gitignored)
│   ├── config.example.json          # Template
│   ├── credentials.json             # Gmail OAuth (gitignored)
│   └── token.pickle                 # Gmail token (gitignored)
├── modules/
│   ├── __init__.py
│   ├── gmail.py                     # Gmail API client
│   ├── email_processor.py           # Email content extraction
│   ├── ai_summarizer.py             # Claude API integration
│   ├── document_generator.py        # Word doc creation
│   ├── tracker.py                   # SQLite tracking
│   ├── cusd_summarizer.py           # Main orchestrator
│   └── logger.py                    # Logging configuration
├── data/
│   └── processed_emails.db          # SQLite database (gitignored)
├── output/
│   └── *.docx                       # Generated digests (gitignored)
├── requirements.txt
├── .gitignore
└── README.md
```

## Future Enhancements

Potential improvements:
- [ ] Forward-looking events (2-week calendar from historical emails)
- [ ] OCR for inline images
- [ ] iCalendar export (.ics files)
- [ ] Email sending integration
- [ ] Web dashboard
- [ ] Multi-label support (HOA, work, etc.)

## License

MIT License - See LICENSE file

## Author

Built for personal use to manage kindergarten parent communications.

## Acknowledgments

- Claude API by Anthropic for AI-powered extraction
- Gmail API by Google for email access
- python-docx for Word document generation
