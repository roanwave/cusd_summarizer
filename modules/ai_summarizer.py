"""AI-powered email summarization using Anthropic Claude."""
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import re

import anthropic

from .email_processor import EmailContent
from .logger import get_logger

logger = get_logger('ai_summarizer')


class AISummarizer:
    """AI-powered email content summarizer."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        prompts: Dict[str, str] = None
    ):
        """Initialize AI summarizer.

        Args:
            api_key: Anthropic API key.
            model: Claude model to use.
            prompts: Profile-specific prompts dictionary.
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.prompts = prompts or {}
        logger.info(f"Initialized AI summarizer with model: {model}")
    
    def summarize_email(self, email: EmailContent) -> Dict[str, Any]:
        """Summarize a single email including images.
        
        Args:
            email: EmailContent object to summarize.
            
        Returns:
            Dictionary with summary, events, action_items, importance.
        """
        logger.info(f"Summarizing email: {email.subject}")
        
        # Build prompt messages
        messages = self._build_email_prompt(email)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                temperature=0,
                messages=messages
            )
            
            # Parse response
            response_text = response.content[0].text
            logger.debug(f"AI Response for {email.message_id}: {response_text[:200]}")
            
            summary_data = self._parse_summary_response(response_text)
            
            # Add metadata
            summary_data['message_id'] = email.message_id
            summary_data['subject'] = email.subject
            summary_data['sender'] = email.sender
            summary_data['date'] = email.date
            
            # Log what was extracted
            logger.info(f"Successfully summarized email {email.message_id}: "
                       f"summary={len(summary_data.get('summary', ''))} chars, "
                       f"events={len(summary_data.get('events', []))}, "
                       f"actions={len(summary_data.get('action_items', []))}")
            
            return summary_data
            
        except Exception as e:
            logger.error(f"Error summarizing email {email.message_id}: {e}")
            return {
                'message_id': email.message_id,
                'subject': email.subject,
                'sender': email.sender,
                'date': email.date,
                'summary': f"Error generating summary: {str(e)}",
                'events': [],
                'action_items': [],
                'importance': 'medium',
                'error': str(e)
            }
    
    def _build_email_prompt(self, email: EmailContent) -> List[Dict[str, Any]]:
        """Build prompt messages for email summarization.

        Args:
            email: EmailContent object.

        Returns:
            List of message dicts for Claude API.
        """
        # Extract text content
        body_text = email.get_body()

        # Clean HTML if needed
        if '<html' in body_text.lower() or '<body' in body_text.lower():
            body_text = self._clean_html(body_text)

        # Build content blocks
        content_blocks = []

        # Get profile-specific prompts
        email_user_template = self.prompts.get('email_user_template', '')

        # Build the text prompt using the template
        text_prompt = email_user_template.format(
            sender=email.sender,
            subject=email.subject,
            date=email.date,
            body=body_text
        )

        content_blocks.append({
            "type": "text",
            "text": text_prompt
        })
        
        # Add images if present
        if email.has_images():
            image_instruction_template = self.prompts.get('image_instruction', 'Image {index}: {filename}')
            max_images = len(email.images)  # Process all filtered images
            logger.info(f"Adding {min(len(email.images), max_images)} images to analysis")

            for idx, img in enumerate(email.images[:max_images]):
                try:
                    # Encode image to base64
                    img_b64 = base64.b64encode(img['data']).decode('utf-8')

                    content_blocks.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": img['mime_type'],
                            "data": img_b64
                        }
                    })

                    # Add image instruction
                    image_instruction = image_instruction_template.format(
                        index=idx + 1,
                        filename=img.get('filename', 'inline image')
                    )

                    content_blocks.append({
                        "type": "text",
                        "text": image_instruction
                    })

                except Exception as e:
                    logger.error(f"Error encoding image {idx}: {e}")

        # Add PDF attachment text if present
        if email.has_attachments():
            pdf_instruction_template = self.prompts.get('pdf_instruction', 'PDF Attachment: {filename}')
            for attachment in email.attachments:
                if attachment.get('extracted_text'):
                    filename = attachment.get('filename', 'document.pdf')
                    extracted_text = attachment['extracted_text']

                    logger.info(f"Adding PDF text from {filename} ({len(extracted_text)} chars)")

                    # Add PDF instruction
                    pdf_instruction = pdf_instruction_template.format(filename=filename)

                    content_blocks.append({
                        "type": "text",
                        "text": f"{pdf_instruction}\n\n{extracted_text}"
                    })
        
        return [
            {
                "role": "user",
                "content": content_blocks
            }
        ]
    
    def _clean_html(self, html: str) -> str:
        """Remove HTML tags and extract text content.
        
        Args:
            html: HTML string.
            
        Returns:
            Plain text content.
        """
        # Simple HTML tag removal
        import re
        
        # Remove script and style elements
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _parse_summary_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from Claude.
        
        Args:
            response_text: Response text from Claude.
            
        Returns:
            Parsed summary dictionary.
        """
        try:
            # Try to find JSON in response
            # Look for JSON between ```json and ``` or just raw JSON
            json_match = response_text
            
            if '```json' in response_text:
                json_match = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                json_match = response_text.split('```')[1].split('```')[0]
            
            data = json.loads(json_match.strip())
            
            # Ensure required fields exist with meaningful defaults
            if 'summary' not in data or not data['summary']:
                data['summary'] = 'Email processed - see events and action items below.'
                logger.warning("No summary in AI response, using default")
            
            data.setdefault('events', [])
            data.setdefault('action_items', [])
            data.setdefault('importance', 'medium')
            data.setdefault('key_dates', [])
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Response text (first 1000 chars): {response_text[:1000]}")
            
            # Try to extract summary from non-JSON text
            summary = response_text[:500] if response_text else "Unable to generate summary"
            
            # Return basic summary if JSON parsing fails
            return {
                'summary': summary,
                'events': [],
                'action_items': [],
                'importance': 'medium',
                'key_dates': []
            }
    
    def create_digest(
        self,
        email_summaries: List[Dict[str, Any]],
        date_range: str
    ) -> Dict[str, Any]:
        """Create consolidated digest from multiple email summaries.

        Args:
            email_summaries: List of email summary dicts.
            date_range: Date range being summarized (e.g., "Oct 10-13, 2025").

        Returns:
            Digest dictionary with executive summary and aggregated content.
        """
        logger.info(f"Creating digest from {len(email_summaries)} email summaries")

        if not email_summaries:
            return {
                'executive_summary': 'No new emails in this period.',
                'event_calendar': [],
                'action_items': [],
                'important_announcements': []
            }

        # Build digest prompt using profile template
        summaries_text = json.dumps(email_summaries, indent=2)

        digest_prompt_template = self.prompts.get('digest_prompt_template', '')
        prompt = digest_prompt_template.format(
            date_range=date_range,
            email_count=len(email_summaries),
            summaries_json=summaries_text[:15000]  # Limit to avoid token overflow
        )

        # Fallback if no template (shouldn't happen but safety net)
        if not prompt:
            prompt = f"""You are creating a comprehensive digest.

Date Range: {date_range}
Number of Emails: {len(email_summaries)}

Raw Email Data (each email already filtered for kindergarten + school-wide content):
{summaries_text[:15000]}

**YOUR TASK: CREATE AN ACTIONABLE DIGEST**

Analyze all emails and create a digest with THREE sections:

## SECTION 1: UPCOMING EVENTS (Chronological Calendar)
Combine information from multiple emails about the SAME event into ONE comprehensive entry.
PRESERVE all DIFFERENT events as separate entries.

For each unique event, provide:
- Full event name
- Complete date/time (with day of week)
- Location
- ALL relevant details from ANY email mentioning it (schedule changes, what to bring, permissions, costs, dress code)
- Source emails that mentioned it

**CRITICAL**: If the raw email data contains events for Monday, Tuesday, Thursday, and Friday, your event_calendar MUST have entries for ALL FOUR days. Do not drop events. Each distinct event (different date or different name) must be included.

**CRITICAL**: If multiple emails mention the same event (e.g., "Raven Run" mentioned in 3 emails), COMBINE all details into ONE event entry. Do not list it 3 times.

## SECTION 2: ACTION ITEMS (What Parents Must Do)
Extract specific actions requiring parent response:
- Sign-up deadlines
- Permission slips due
- Items to bring/purchase
- Volunteer opportunities
- Conference scheduling

## SECTION 3: IMPORTANT ANNOUNCEMENTS
Extract key information that is not an event or action:
- Schedule changes
- Policy updates  
- General reminders
- Future planning notices

**CRITICAL RULES:**

1. **DEDUPLICATE EVENTS**: "Raven Run" mentioned in 3 emails = 1 event entry with combined details
2. **BE SPECIFIC**: Use exact event names, dates, times from the emails
3. **CONSOLIDATE DETAILS**: If Email A says "Raven Run Monday" and Email B says "Raven Run at 1:45 PM on school field", combine into: "Raven Run on Monday, October 27th at 1:45 PM on the school field"
4. **WEDNESDAY EARLY RELEASE**: Mark as LOW priority, note ELC attendance (no pickup change)
5. **NO VAGUE DESCRIPTIONS**: Every event must have a specific name, not "field trip" but "Pumpkin Patch Field Trip"

Return as JSON:
{{
  "executive_summary": "2-3 sentence overview of the week\\'s most important items",
  "event_calendar": [
    {{
      "title": "Specific event name (e.g., 'Raven Run', not 'running event')",
      "date": "Full date with day (e.g., 'Monday, October 27th')",
      "time": "Exact time or range (e.g., '1:45 PM' or '7:45 AM - 11:45 AM')",  
      "location": "Specific location",
      "details": "COMPREHENSIVE details: schedule modifications, items needed, permissions, costs, dress code, transportation - combine info from all emails mentioning this event",
      "sources": ["List of email subjects that mentioned this event"]
    }}
  ],
  "action_items": [
    {{
      "action": "Specific action parents must take",
      "due_date": "Exact deadline",
      "priority": "high/medium/low (low for Wednesday early release)",
      "details": "Additional context or instructions"
    }}
  ],
  "important_announcements": [
    "String with announcement text - NOT a dict, just the text itself"
  ]
}}

**EXAMPLE OF GOOD EVENT CONSOLIDATION:**

If you see:
- Email 1: "Raven Run on Monday"  
- Email 2: "PM Kindergarten Raven Run at 1:45"
- Email 3: "Raven Run event at school field, families welcome"

Create ONE event:
{{
  "title": "Raven Run",
  "date": "Monday, October 27th",
  "time": "1:45 PM",
  "location": "School field",
  "details": "PM Kindergarten students will participate. Parents and families welcome to cheer from the field without checking in at office.",
  "sources": ["Email 1 subject", "Email 2 subject", "Email 3 subject"]
}}

**CRITICAL**: important_announcements should be an array of STRINGS, not dicts. Just: ["Announcement text here", "Another announcement"]

Focus on being specific, comprehensive, and actionable. Parents need to know EXACTLY what\\'s happening and what they need to do."""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            response_text = response.content[0].text
            digest = self._parse_summary_response(response_text)
            
            logger.info("Successfully created consolidated digest")
            return digest
            
        except Exception as e:
            logger.error(f"Error creating digest: {e}")
            return {
                'executive_summary': f'Error creating digest: {str(e)}',
                'event_calendar': [],
                'action_items': [],
                'important_announcements': [],
                'error': str(e)
            }
