# Context Prompt for HOA Email Summarizer (Next Session)

## Quick Start

I have a working CUSD (school) email summarizer and want to clone it for HOA emails. 

**GitHub Repository:** https://github.com/yourusername/cusd-summarizer

Please review the repository to understand the complete working system, then help me:
1. Clone it for HOA emails (different label, content focus)
2. Handle inline images appropriately (HOA emails have lots of them)
3. Keep both systems maintainable

## Key Repository Files to Review

### Essential Documentation
- **README.md** - Complete overview, features, usage
- **ARCHITECTURE.md** - Technical deep dive, all modules explained
- **requirements.txt** - Dependencies

### Core Modules
- **modules/ai_summarizer.py** - Claude API integration (CRITICAL - shows working prompts)
- **modules/document_generator.py** - Word doc creation with tables
- **modules/gmail.py** - Gmail API integration
- **modules/email_processor.py** - Content extraction (handles images)
- **modules/tracker.py** - SQLite tracking

### Configuration
- **config/config.example.json** - Configuration template

## What's Working (CUSD System)

✅ Gmail OAuth 2.0 authentication
✅ Email fetching with label filter
✅ Text extraction (8000 char limit)
✅ Claude AI JSON extraction (events, action items, dates)
✅ Word document generation with professional tables
✅ SQLite tracking (no duplicates)
✅ Markdown cleanup
✅ Multi-event detection

## Critical Lesson Learned (MUST READ)

The prompting strategy went through many iterations. **The key to success was keeping prompts SHORT and CRYSTAL CLEAR about JSON output.**

From `modules/ai_summarizer.py`:
```python
system_prompt = """You are a JSON data extractor for school emails.

CRITICAL: Your response MUST be ONLY valid JSON. No markdown, no explanations.

...

CRITICAL OUTPUT REQUIREMENT: Return ONLY the JSON object. Just raw JSON starting with {
"""
```

❌ **What failed:** Long chatty prompts with examples, saying "plain text" when needing JSON
✅ **What works:** Short, direct, JSON-only emphasis repeated 3 times

See ARCHITECTURE.md for full details.

## New Requirement: HOA Email Summarizer

### What Needs to Change

**Label:** "CUSD" → "HOA"
**Context:** "kindergarten student" → "homeowner"
**Focus:** Board meetings, assessments, maintenance, architectural reviews
**Filtering:** Remove kindergarten/grade-specific logic
**Images:** HOA emails have LOTS of inline images (JPG, PNG, PDF)

### Key Decision Needed

**Image Handling Strategy:**

Option A: Ignore (like CUSD does)
Option B: OCR text extraction
Option C: Send to Claude Vision API
Option D: Note presence only

Current email_processor.py already extracts images (base64), just not sent to AI.

### Architecture Question

Should this be:
1. **Separate clone** - `hoa_summarizer/` directory, duplicate modules
2. **Shared modules** - Generic system with config parameter for label/context
3. **Hybrid** - Shared base modules, label-specific customizations

## What I Need Help With

1. Review the GitHub repo to understand current architecture
2. Recommend best approach (separate vs shared)
3. Guide implementation step-by-step
4. Handle image strategy
5. Test with actual HOA emails

## Technical Context

- **Python 3.x** on Windows
- **APIs:** Gmail (OAuth 2.0), Anthropic Claude (Sonnet 4.5)
- **Database:** SQLite
- **Output:** Word documents
- **Current location:** `C:\Users\erick\py\cusd_summarizer\`

## Success Criteria

- Process "HOA" labeled emails
- Extract meeting dates, deadlines, maintenance schedules
- Generate Word document digest
- Track processed emails independently
- Don't break existing CUSD system
- Minimal code duplication

## Request

Help me clone the CUSD system for HOA emails. Start by reviewing the repo, then recommend the best architecture approach. Let's keep it maintainable since I'm not a professional coder.

## Repository Structure Reference

```
cusd_summarizer/
├── README.md              # Overview, setup, usage
├── ARCHITECTURE.md        # Technical details, all modules
├── requirements.txt       # Dependencies
├── LICENSE                # MIT
├── .gitignore            # Ignore configs, data, output
├── main.py               # Entry point
├── config/
│   └── config.example.json
└── modules/
    ├── gmail.py
    ├── email_processor.py
    ├── ai_summarizer.py      # CRITICAL - working prompts
    ├── document_generator.py
    ├── tracker.py
    ├── cusd_summarizer.py    # Orchestrator
    └── logger.py
```
