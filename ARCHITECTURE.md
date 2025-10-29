# CUSD Summarizer - Technical Architecture

## System Flow

```
┌─────────────────┐
│   Gmail API     │
│  (OAuth 2.0)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Email Processor │
│  - Extract text │
│  - Parse HTML   │
│  - Get images   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  AI Summarizer  │◄────►│  Claude API  │
│  - Build prompt │      │  (Sonnet 4.5)│
│  - Parse JSON   │      └──────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Document Generator│
│  - Events table │
│  - Formatting   │
│  - Word output  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Tracker DB     │
│  (SQLite)       │
│  - Dedupe       │
│  - History      │
└─────────────────┘
```

## Module Details

### gmail.py - Gmail API Integration

**Purpose:** Authenticate and fetch emails from Gmail

**Key Methods:**
- `authenticate()` - OAuth 2.0 flow, creates token.pickle
- `get_messages_with_label()` - Fetch messages by label name
- `get_message_details()` - Get full message content
- `send_message()` - Send digest via email (optional)

**Dependencies:**
- google-auth
- google-api-python-client

**Configuration:**
- credentials.json (from Google Cloud Console)
- token.pickle (auto-generated on first auth)

**Rate Limits:**
- Gmail API: 250 quota units per user per second
- Message fetch: 5 units per request
- Recommend: batch requests, respect rate limits

### email_processor.py - Content Extraction

**Purpose:** Parse email messages and extract content

**Key Methods:**
- `process_message()` - Main processing entry point
- `_extract_text_from_html()` - Strip HTML tags, get plain text
- `_extract_images()` - Get inline images (base64 encoded)
- `_extract_attachments()` - Handle PDF/other attachments

**Content Handling:**
- Text: Extracted from both text/plain and text/html parts
- HTML: Cleaned with regex to remove scripts/styles
- Images: Stored as base64, noted in summary (not sent to AI currently)
- Attachments: Metadata captured, content available

**Character Limits:**
- Body text: 8000 chars (configurable)
- Subject: No limit
- Sender: No limit

### ai_summarizer.py - Claude API Integration

**Purpose:** Send emails to Claude for structured data extraction

**Key Methods:**
- `summarize_email()` - Extract JSON from single email
- `create_digest()` - Consolidate multiple summaries
- `_parse_summary_response()` - Parse JSON, handle errors

**Prompting Strategy:**

**System Prompt (Individual Emails):**
```python
"""You are a JSON data extractor for school emails.

CRITICAL: Your response MUST be ONLY valid JSON. No markdown, no explanations.

Extract: summary, events, action_items, importance, key_dates

For multi-day emails, create SEPARATE event objects for EACH day.

JSON schema:
{
  "summary": "3-5 sentences",
  "events": [
    {
      "title": "Specific name",
      "date": "Day, Month Date",
      "time": "Exact time",
      "location": "Location",
      "description": "All details",
      "priority": "high/medium/low",
      "scope": "kindergarten-specific / school-wide"
    }
  ],
  "action_items": [...],
  "importance": "high/medium/low",
  "key_dates": [...]
}

CRITICAL: Return ONLY the JSON object. Just raw JSON starting with {
"""
```

**User Prompt:**
```python
f"""Email from: {email.sender}
Subject: {email.subject}
Date: {email.date}

Content:
{body_text[:8000]}

Please analyze this school email and extract ALL SPECIFIC DETAILS about kindergarten-relevant AND school-wide events.

OUTPUT ONLY JSON - NO MARKDOWN, NO EXPLANATIONS.
"""
```

**Digest Consolidation Prompt:**
- Takes all individual email JSONs
- Creates unified executive summary
- Merges events (deduplicates by title+date)
- Aggregates action items
- Extracts announcements

**Error Handling:**
- JSON parsing failures logged
- Fallback to text summary (500 char limit)
- Returns empty arrays for missing fields

**Token Limits:**
- Individual emails: 3000 tokens output
- Digest: 4000 tokens output
- Input: ~1500-2500 tokens per email (8000 chars)

### document_generator.py - Word Document Creation

**Purpose:** Generate formatted Word documents

**Key Methods:**
- `create_digest_document()` - Main entry point
- `_add_digest()` - Executive summary, events, actions
- `_add_email_summaries()` - Individual email sections
- `_clean_markdown()` - Strip ##, **, *, - formatting

**Document Structure:**

1. **Title**
   - "CUSD Email Digest - [Date]"
   - Byline: "Compiled by CUSD Email Summarizer"

2. **Executive Summary**
   - Paragraph text
   - 3-5 sentences

3. **Upcoming Events**
   - Word table (4 columns)
   - Headers: Event | Date | Time | Location
   - Column widths: 2.5" | 1.8" | 1.2" | 1.5"
   - Style: 'Light Grid Accent 1'

4. **Event Details**
   - Bold event names
   - Paragraph descriptions
   - Source attribution (9pt font)

5. **Action Items**
   - Priority emoji: 🔴 HIGH, 🟡 MEDIUM, 🟢 LOW
   - Due dates in parentheses
   - Details in 10pt font

6. **Important Announcements**
   - Bullet list

7. **Page Break**

8. **Individual Email Summaries**
   - H3: Subject
   - Metadata: From, Date
   - Summary text (markdown cleaned)

**Formatting:**
- Font: Default (Calibri)
- Headers: Bold, larger
- Tables: Professional styling
- Spacing: Paragraph breaks

**Truncation Handling:**
- Long paragraphs (>1000 chars) split automatically
- Prevents python-docx truncation issues

### tracker.py - Database Management

**Purpose:** Track processed emails, avoid duplicates

**Database Schema:**

```sql
CREATE TABLE processed_emails (
    message_id TEXT PRIMARY KEY,
    subject TEXT,
    sender TEXT,
    received_date TEXT,
    processed_date TEXT,
    summary TEXT,  -- JSON string of extracted data
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

**Key Methods:**
- `is_processed()` - Check if email already processed
- `mark_processed()` - Add email to database
- `save_digest()` - Store digest metadata
- `cleanup_old_records()` - Optional data retention

**Indexes:**
- Primary key on message_id (fast lookups)
- Index on processed_date (for cleanup)

### cusd_summarizer.py - Main Orchestrator

**Purpose:** Coordinate all components

**Workflow:**

```python
def main():
    # 1. Initialize components
    gmail = GmailClient()
    processor = EmailProcessor()
    summarizer = AISummarizer()
    generator = DocumentGenerator()
    tracker = Tracker()
    
    # 2. Fetch emails
    messages = gmail.get_messages_with_label("CUSD")
    
    # 3. Filter unprocessed
    unprocessed = [m for m in messages if not tracker.is_processed(m)]
    
    # 4. Process each email
    summaries = []
    for message in unprocessed:
        email = processor.process_message(message)
        summary = summarizer.summarize_email(email)
        summaries.append(summary)
        tracker.mark_processed(message, summary)
    
    # 5. Create digest
    digest = summarizer.create_digest(summaries, date_range)
    
    # 6. Generate document
    output_path = generator.create_digest_document(
        emails=processed_emails,
        consolidated_digest=digest
    )
    
    # 7. Save digest metadata
    tracker.save_digest(digest_id, date_range, output_path)
    
    # 8. Optional: Send email
    if config.get("send_email"):
        gmail.send_message(output_path)
```

**Error Handling:**
- Try-catch around each major step
- Logging at INFO/ERROR levels
- Graceful degradation (continue on non-critical errors)

**Command Line Arguments:**
- `--force` - Reprocess all emails
- `--stats` - Show statistics only
- `--config` - Use alternate config file

## Configuration Management

**config.json Structure:**

```json
{
  "gmail": {
    "credentials_file": "path/to/credentials.json",
    "token_file": "path/to/token.pickle",
    "label": "CUSD"
  },
  "anthropic": {
    "api_key": "sk-ant-...",
    "model": "claude-sonnet-4-20250514"
  },
  "processing": {
    "lookback_hours": 72,
    "max_emails": 50,
    "body_char_limit": 8000
  },
  "output": {
    "directory": "output",
    "email_to": "user@example.com"
  },
  "database": {
    "path": "data/processed_emails.db"
  }
}
```

**Environment Variables (Alternative):**
- `ANTHROPIC_API_KEY` - Can override config
- `GMAIL_CREDENTIALS` - Path to credentials.json
- `DATABASE_PATH` - Path to SQLite database

## Error Handling & Logging

**Logging Levels:**
- DEBUG: Detailed processing info
- INFO: Major steps, counts, success messages
- WARNING: Non-critical issues (missing fields, parsing quirks)
- ERROR: Failed operations (API errors, JSON parsing)

**Log Format:**
```
2025-10-27 10:41:16 - cusd_summarizer - INFO - Processing 21 emails
2025-10-27 10:41:29 - ai_summarizer - ERROR - Error parsing JSON response
2025-10-27 10:41:29 - ai_summarizer - ERROR - Response text (first 1000 chars): ...
```

**Critical Errors:**
- Gmail authentication failure → Exit with message
- Anthropic API key invalid → Exit with message
- Database locked → Retry 3x, then exit

**Recoverable Errors:**
- Single email JSON parsing fails → Use fallback summary, continue
- Image extraction fails → Note in summary, continue
- Document generation partial failure → Save what's possible

## Performance Considerations

**Bottlenecks:**
1. **AI API calls** - 2-3 seconds per email
2. **Gmail API** - Network latency for message fetching
3. **Document generation** - Minimal (~100ms)

**Optimization Strategies:**
- Batch email fetching where possible
- Cache processed emails in database
- Skip already-processed messages
- Limit lookback window to reduce processing

**Typical Run Times:**
- 10 new emails: ~45 seconds (30s AI, 10s Gmail, 5s other)
- 20 new emails: ~90 seconds
- 50 emails (--force): ~4 minutes

**Memory Usage:**
- Typical: <100 MB
- Peak: ~200 MB (with large attachments)

## Security Considerations

**API Keys:**
- Store in config.json (gitignored)
- Never commit to repository
- Rotate periodically

**Gmail OAuth:**
- token.pickle contains OAuth token
- gitignored, local only
- Expires after ~7 days of inactivity
- Re-auth required if expired

**Database:**
- Contains email metadata and summaries
- No passwords or sensitive credentials
- Personal data only
- gitignored

**Recommendations:**
- Use separate Google account for automation
- Limit Gmail API scopes to minimum required
- Review API key usage regularly
- Encrypt database at rest (OS-level)

## Testing Strategy

**Unit Tests:**
- Email processor: Test HTML stripping, text extraction
- AI summarizer: Mock API responses, test JSON parsing
- Document generator: Test table creation, formatting
- Tracker: Test database operations, deduplication

**Integration Tests:**
- Full pipeline with test emails
- Gmail API with test account
- AI API with small test set

**Manual Testing:**
- Run with --force on known email set
- Verify output document quality
- Check event extraction accuracy
- Review action item priorities

## Deployment

**Development:**
```bash
python main.py --force  # Test with all emails
```

**Production:**
```bash
python main.py          # Normal run
```

**Scheduled (Windows Task Scheduler):**
```powershell
Action: python.exe
Arguments: C:\path\to\cusd_summarizer\main.py
Start in: C:\path\to\cusd_summarizer
Trigger: Daily at 6:00 AM
```

**Scheduled (Linux cron):**
```bash
0 6 * * * cd /path/to/cusd_summarizer && python main.py
```

## Troubleshooting Guide

**Issue: "Error parsing JSON response"**
- Check logs for actual AI response
- Verify prompt doesn't have conflicting instructions
- Ensure model is claude-sonnet-4-20250514

**Issue: Missing events in table**
- Check individual email summary for event extraction
- Verify events have proper JSON structure
- Look for "events=0" in logs

**Issue: Email content truncated**
- Increase body_char_limit in config
- Check for paragraph splitting in document_generator
- Verify no HTML artifacts breaking content

**Issue: Gmail authentication failed**
- Delete token.pickle
- Re-run to trigger OAuth flow
- Verify credentials.json is valid

**Issue: Database locked**
- Close any open DB connections
- Check for multiple running instances
- Restart if persistent

## Future Architecture Considerations

**Scalability:**
- Current: Single-user, local execution
- Future: Multi-user, cloud deployment
- Considerations: User isolation, rate limits, cost allocation

**Multi-Label Support:**
- Current: Single label (CUSD)
- Future: Multiple labels (CUSD, HOA, Work, etc.)
- Architecture: Generic system with label-specific configs

**Real-Time Processing:**
- Current: Batch processing on demand
- Future: Gmail push notifications → immediate processing
- Architecture: Webhook receiver, queue system

**Web Interface:**
- Current: Command line only
- Future: Web dashboard
- Tech stack: Flask/FastAPI + React frontend
