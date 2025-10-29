# Multi-Profile Implementation Summary

## What We've Implemented

### ✅ Completed Components

#### 1. Profile Configuration System
- **Created**: `profiles/cusd.json` and `profiles/hoa.json`
- **Features**:
  - Profile-specific Gmail labels, lookback hours
  - Custom AI prompts (email_system, email_user_template, image_instruction, pdf_instruction, digest_prompt_template)
  - Document section definitions
  - Separate output directories and databases per profile

#### 2. Enhanced Config Manager (`modules/config_manager.py`)
- **Added**: Profile parameter to constructor
- **Features**:
  - Loads base config + profile-specific config
  - Merges configurations (profile overrides base)
  - Validates profile requirements

#### 3. Image Filtering (`modules/email_processor.py`)
- **Added**: `min_image_width` and `min_image_height` parameters
- **Features**:
  - Filters out images smaller than 150x150px (signatures, logos)
  - Uses PIL to check dimensions before processing
  - Logs filtered images for transparency

#### 4. PDF Processing (`modules/email_processor.py`)
- **Added**: PDF text extraction capability
- **Features**:
  - Downloads PDF attachments via Gmail API
  - Extracts text using pypdf/PyPDF2
  - Limits extraction to 10,000 chars to avoid huge PDFs
  - Adds extracted text to email content for AI analysis

#### 5. Profile-Aware AI Summarizer (`modules/ai_summarizer.py`)
- **Added**: Prompts parameter to constructor
- **Features**:
  - Uses profile-specific prompts from config
  - Template-based prompt formatting
  - Supports PDF attachment content in analysis
  - Configurable max_images per email

### 🔧 Remaining Work

#### 1. Update Document Generator
**File**: `modules/document_generator.py`
**Changes Needed**:
- Add `profile_config` parameter to constructor
- Read section definitions from profile config
- Add HOA-specific section handlers:
  - `_add_compliance_items()` - Violations, deadlines, consequences
  - `_add_financial_notices()` - Dues, assessments, payments
  - `_add_maintenance_schedule()` - Closures, construction, impact

**Example**:
```python
def __init__(self, output_dir: str = "output", profile_config: dict = None):
    self.output_dir = output_dir
    self.profile_config = profile_config or {}
    self.doc = Document()

def _add_digest(self, digest):
    # Read sections from profile config
    sections = self.profile_config.get('document', {}).get('sections', [])

    for section in sections:
        section_name = section['name']
        if section_name == 'compliance_items':
            self._add_compliance_items(digest)
        elif section_name == 'financial_notices':
            self._add_financial_notices(digest)
        # ... etc
```

#### 2. Update Main Orchestrator
**File**: `modules/cusd_summarizer.py`
**Changes Needed**:
- Add `--profile` command-line argument
- Pass profile to `get_config()`
- Update component initialization with profile-specific settings
- Pass profile config to AI summarizer and document generator

**Example**:
```python
def __init__(self, config_path: str = None, profile: str = None):
    # Load configuration with profile
    self.config = get_config(config_path, profile)

    # ... existing code ...

    # AI summarizer with profile prompts
    prompts = self.config.get('prompts')
    self.ai_summarizer = AISummarizer(
        api_key=api_key,
        model=model,
        prompts=prompts
    )

    # Email processor with profile settings
    process_pdfs = self.config.get('processing', 'process_pdfs')
    min_image_width = self.config.get('processing', 'min_image_width')
    min_image_height = self.config.get('processing', 'min_image_height')

    self.email_processor = EmailProcessor(
        gmail_client=self.gmail_client,
        max_image_size_mb=max_image_size,
        min_image_width=min_image_width,
        min_image_height=min_image_height,
        process_pdfs=process_pdfs
    )

def main():
    parser.add_argument(
        '--profile',
        type=str,
        default='cusd',
        help='Profile to use (cusd, hoa, etc.)'
    )
```

#### 3. Update Database Schema
**File**: `modules/tracker.py`
**Changes Needed**:
- Add `profile` column to `processed_emails` table
- Add `profile` column to `digests` table
- Filter queries by profile to keep data separate

**Example**:
```python
CREATE TABLE processed_emails (
    message_id TEXT PRIMARY KEY,
    profile TEXT NOT NULL,  -- NEW
    subject TEXT,
    ...
);

CREATE TABLE digests (
    digest_id TEXT PRIMARY KEY,
    profile TEXT NOT NULL,  -- NEW
    created_date TEXT,
    ...
);
```

#### 4. Update Requirements
**File**: `requirements.txt`
**Add**:
```
pypdf>=4.0.0
Pillow>=10.0.0  # Already might be there for image handling
```

## Usage Examples

### CUSD Profile (School Emails)
```bash
# Default profile (CUSD)
python main.py

# Explicit CUSD profile
python main.py --profile cusd

# Force reprocess all CUSD emails
python main.py --profile cusd --force
```

### HOA Profile (Homeowners Association)
```bash
# Run HOA summarizer
python main.py --profile hoa

# Force reprocess all HOA emails
python main.py --profile hoa --force

# Show HOA statistics
python main.py --profile hoa --stats
```

## Key Architectural Decisions

### Why Profile-Based Instead of Separate Codebases?
1. **Maintainability**: Single codebase easier to update and debug
2. **Code Reuse**: 80% of code is shared (Gmail API, AI integration, document generation)
3. **Flexibility**: Easy to add new profiles (work, personal, etc.)
4. **Configuration**: Profile-specific behavior via JSON, not code changes

### Why Separate Databases?
1. **Data Isolation**: CUSD and HOA data kept completely separate
2. **Privacy**: No cross-contamination of email metadata
3. **Performance**: Smaller databases = faster queries
4. **Backup**: Can backup/restore profiles independently

### Why Template-Based Prompts?
1. **Customization**: Easy to tune prompts per profile without code changes
2. **Context-Aware**: HOA prompts focus on compliance/financials vs. school events
3. **Experimentation**: Test different prompt strategies via config edits
4. **Version Control**: Prompt changes tracked in JSON, not Python code

## HOA-Specific Features

### Image Analysis Enhancements
- **Event flyers**: Pool party, board meeting announcements
- **Violation photos**: Lawn issues, parking violations, trash bins
- **Financial charts**: Budget breakdowns, assessment notices
- **Maps**: Construction zones, facility closures
- **Community notices**: Clubhouse hours, amenity updates

### PDF Processing
- **Newsletters**: Monthly HOA newsletters with multiple sections
- **Financial docs**: Budget reports, assessment notices, dues statements
- **Meeting minutes**: Board meeting agendas and minutes
- **Compliance letters**: Violation notices, architectural approval forms
- **Maintenance schedules**: Pool closures, landscaping work, construction timelines

### Document Sections (HOA)
1. **Executive Summary**: Top priorities requiring immediate attention
2. **Compliance Items**: Violations, deadlines, consequences, contacts
3. **Financial Notices**: Dues, assessments, amounts, due dates
4. **Upcoming Events**: Community meetings, social events, board meetings
5. **Maintenance Schedule**: Closures, construction, resident impact
6. **Action Items**: Required homeowner actions with deadlines
7. **Important Announcements**: Policy changes, reminders, updates

## Testing Checklist

### CUSD Profile Testing
- [ ] Fetches emails with "CUSD" label
- [ ] Filters out small images (signatures)
- [ ] Extracts kindergarten + school-wide events
- [ ] Creates separate database: `data/cusd_emails.db`
- [ ] Outputs to: `output/cusd/CUSD_Digest_[date].docx`
- [ ] Uses CUSD-specific prompts and sections

### HOA Profile Testing
- [ ] Fetches emails with "HOA" label
- [ ] Processes inline images (flyers, charts, photos)
- [ ] Downloads and extracts PDF text
- [ ] Identifies compliance, financial, and maintenance items
- [ ] Creates separate database: `data/hoa_emails.db`
- [ ] Outputs to: `output/hoa/HOA_Digest_[date].docx`
- [ ] Uses HOA-specific prompts and sections

## Next Steps

1. **Complete document_generator.py updates** (add HOA section handlers)
2. **Update cusd_summarizer.py** (add profile argument)
3. **Update tracker.py** (add profile column to database)
4. **Add pypdf to requirements.txt**
5. **Test CUSD profile** (ensure no regressions)
6. **Test HOA profile** (end-to-end with real HOA emails)
7. **Update README.md** with multi-profile usage instructions

## Configuration Reference

### Base Config (`config/config.json`)
- Default profile setting
- Gmail OAuth scopes
- AI model configuration
- Global settings (retention, scheduling)

### Profile Config (`profiles/{name}.json`)
- Gmail label and lookback hours
- Image/PDF processing settings
- AI prompts (customized for context)
- Document sections and formatting
- Profile-specific output and database paths

### Environment Variables
- `ANTHROPIC_API_KEY`: Claude API key (required)
- Gmail credentials: `config/credentials.json` (downloaded from Google Cloud)
- Gmail token: `config/token.pickle` (auto-generated on first run)
