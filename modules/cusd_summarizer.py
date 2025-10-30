"""Main application orchestrator for CUSD Email Summarizer."""
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import copy

from .config_manager import get_config
from .logger import setup_logging, get_logger
from .gmail_client import GmailClient
from .email_processor import EmailProcessor, EmailContent
from .ai_summarizer import AISummarizer
from .tracker import EmailTracker
from .document_generator import DocumentGenerator


class CUSDSummarizer:
    """Main application class for CUSD email summarization."""

    def __init__(self, config_path: str = None, profile: str = None):
        """Initialize the summarizer application.

        Args:
            config_path: Optional path to config file.
            profile: Profile name to use (e.g., 'cusd', 'hoa').
        """
        # Load configuration with profile
        from .config_manager import reset_config
        reset_config()  # Reset global config to allow profile switching
        self.config = get_config(config_path, profile)
        self.profile = self.config.profile_name
        
        # Setup logging
        log_file = self.config.resolve_path(
            self.config.get('logging', 'file')
        )
        log_level = self.config.get('logging', 'level')
        console_output = self.config.get('logging', 'console_output')
        
        self.logger = setup_logging(
            log_file=str(log_file),
            log_level=log_level,
            console_output=console_output
        )
        
        self.logger.info("="*60)
        self.logger.info("CUSD Email Summarizer Starting")
        self.logger.info("="*60)
        
        # Initialize components
        self._init_components()
    
    def _init_components(self):
        """Initialize all application components."""
        # Gmail client
        credentials_file = self.config.resolve_path('config/credentials.json')
        token_file = self.config.resolve_path('config/token.pickle')
        scopes = self.config.get('gmail', 'scopes')

        self.gmail_client = GmailClient(
            credentials_file=str(credentials_file),
            token_file=str(token_file),
            scopes=scopes
        )

        # Email processor with profile-specific settings
        max_image_size = self.config.get('output', 'max_image_size_mb')
        min_image_width = self.config.get('processing', 'min_image_width')
        min_image_height = self.config.get('processing', 'min_image_height')
        process_pdfs = self.config.get('processing', 'process_pdfs')

        self.email_processor = EmailProcessor(
            gmail_client=self.gmail_client,
            max_image_size_mb=max_image_size,
            min_image_width=min_image_width,
            min_image_height=min_image_height,
            process_pdfs=process_pdfs
        )

        # AI summarizer with profile-specific prompts
        api_key = self.config.get_ai_api_key()
        model = self.config.get('ai', 'model')
        prompts = self.config.get('prompts')

        self.ai_summarizer = AISummarizer(
            api_key=api_key,
            model=model,
            prompts=prompts
        )

        # Tracker with profile-specific database
        db_path = self.config.resolve_path(
            self.config.get('database', 'path')
        )
        self.tracker = EmailTracker(db_path=str(db_path))

        # Document generator with profile config
        output_dir = self.config.resolve_path(
            self.config.get('output', 'directory')
        )
        filename_pattern = self.config.get('output', 'filename_pattern')
        self.doc_generator = DocumentGenerator(
            output_dir=str(output_dir),
            filename_pattern=filename_pattern
        )

        self.logger.info(f"All components initialized successfully for profile: {self.profile}")
    
    def run(self, force_reprocess: bool = False) -> Dict[str, Any]:
        """Run the complete summarization pipeline.
        
        Args:
            force_reprocess: If True, reprocess all emails ignoring tracking.
            
        Returns:
            Dictionary with execution results and statistics.
        """
        start_time = datetime.now()
        self.logger.info(f"Starting run at {start_time}")
        
        results = {
            'start_time': start_time.isoformat(),
            'emails_found': 0,
            'emails_processed': 0,
            'emails_skipped': 0,
            'digest_created': False,
            'digest_sent': False,
            'errors': []
        }
        
        try:
            # Step 1: Discover new emails
            label = self.config.get('gmail', 'label')
            lookback_hours = self.config.get('gmail', 'lookback_hours')
            
            # Get already processed IDs unless forcing reprocess
            exclude_ids = [] if force_reprocess else self.tracker.get_all_processed_ids()
            
            self.logger.info(f"Searching for emails with label '{label}'")
            messages = self.gmail_client.list_messages(
                label_name=label,
                lookback_hours=lookback_hours,
                exclude_ids=exclude_ids
            )
            
            results['emails_found'] = len(messages)
            
            if not messages:
                self.logger.info("No new emails to process")
                return results
            
            # Step 2: Retrieve and process email content
            self.logger.info(f"Processing {len(messages)} emails")
            email_contents: List[EmailContent] = []
            
            for msg_meta in messages:
                try:
                    # Get full message
                    full_msg = self.gmail_client.get_message(msg_meta['id'])
                    if not full_msg:
                        self.logger.warning(f"Could not retrieve message {msg_meta['id']}")
                        results['emails_skipped'] += 1
                        continue
                    
                    # Process content
                    email_content = self.email_processor.process_message(full_msg)
                    email_contents.append(email_content)
                    
                except Exception as e:
                    self.logger.error(f"Error processing message {msg_meta['id']}: {e}")
                    results['errors'].append({
                        'message_id': msg_meta['id'],
                        'error': str(e)
                    })
                    results['emails_skipped'] += 1
            
            if not email_contents:
                self.logger.warning("No emails successfully processed")
                return results
            
            # Step 3: Summarize emails with AI
            self.logger.info(f"Summarizing {len(email_contents)} emails with AI")
            email_summaries = []
            
            for email in email_contents:
                try:
                    summary_data = self.ai_summarizer.summarize_email(email)
                    
                    # FIX: Build complete email summary structure with correct field names
                    email_summary = {
                        'message_id': email.message_id,
                        'subject': email.subject,
                        'sender': email.sender,      # document_generator expects 'sender' not 'from'
                        'received': email.date,      # document_generator expects 'received' not 'date'
                        'summary': summary_data      # This is the dict with 'summary', 'events', 'action_items', 'importance'
                    }
                    email_summaries.append(email_summary)
                    
                    # Mark as processed
                    self.tracker.mark_processed(
                        message_id=email.message_id,
                        thread_id=email.thread_id,
                        subject=email.subject,
                        sender=email.sender,
                        summary=json.dumps(summary_data)
                    )
                    
                    results['emails_processed'] += 1
                    
                except Exception as e:
                    self.logger.error(f"Error summarizing email {email.message_id}: {e}")
                    results['errors'].append({
                        'message_id': email.message_id,
                        'error': str(e)
                    })
            
            if not email_summaries:
                self.logger.warning("No emails successfully summarized")
                return results
            
            # Step 4: Create consolidated digest
            self.logger.info("Creating consolidated digest")
            date_str = datetime.now().strftime("%B %d, %Y")
            
            # FIX: Pass a deep copy to prevent create_digest from mutating our email_summaries
            digest_data = self.ai_summarizer.create_digest(
                email_summaries=copy.deepcopy(email_summaries),
                date_range=date_str
            )
            
            # Step 5: Generate document
            self.logger.info("Generating digest document")
            doc_path = self.doc_generator.create_digest_document(
                consolidated_digest=digest_data,
                emails=email_summaries,  # FIX: parameter name is 'emails' not 'email_summaries'
                date=datetime.now()
            )
            
            results['digest_created'] = True
            results['digest_file'] = str(doc_path)
            
            # Save digest to database
            self.tracker.save_digest(
                date=date_str,
                email_count=len(email_summaries),
                digest_file=str(doc_path),
                digest_data=digest_data
            )
            
            # Step 6: Send email (if configured)
            if self.config.get('email', 'send_digest'):
                self.logger.info("Sending digest email")
                
                # Create email body
                email_body = self.doc_generator.create_simple_text_digest(
                    digest_data=digest_data,
                    email_summaries=email_summaries,
                    date_str=date_str
                )
                
                recipient = self.config.get('email', 'recipient')
                subject = self.config.get('email', 'subject_pattern').format(
                    date=date_str
                )
                
                # TODO: Add attachment support to gmail_client.send_email()
                # For now, just send without attachment
                sent = self.gmail_client.send_email(
                    to=recipient,
                    subject=subject,
                    body=email_body + f"\n\nDigest saved to: {doc_path}"
                )
                
                results['digest_sent'] = sent
            
            # Step 7: Cleanup old records
            retention_days = self.config.get('tracking', 'retention_days')
            deleted = self.tracker.cleanup_old_records(retention_days)
            self.logger.info(f"Cleaned up {deleted} old tracking records")
            
        except Exception as e:
            self.logger.error(f"Critical error in run: {e}", exc_info=True)
            results['errors'].append({
                'critical': True,
                'error': str(e)
            })
        
        finally:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            results['end_time'] = end_time.isoformat()
            results['duration_seconds'] = duration
            
            self.logger.info("="*60)
            self.logger.info(f"Run completed in {duration:.2f} seconds")
            self.logger.info(f"Emails found: {results['emails_found']}")
            self.logger.info(f"Emails processed: {results['emails_processed']}")
            self.logger.info(f"Emails skipped: {results['emails_skipped']}")
            self.logger.info(f"Digest created: {results['digest_created']}")
            self.logger.info(f"Errors: {len(results['errors'])}")
            self.logger.info("="*60)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get application statistics.
        
        Returns:
            Dictionary with statistics from tracker.
        """
        return self.tracker.get_stats()
    
    def cleanup(self):
        """Cleanup resources."""
        if hasattr(self, 'tracker'):
            self.tracker.close()
        self.logger.info("Cleanup completed")


def main():
    """Main entry point for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Email Summarizer - Multi-profile automated email digest generator'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to config.json file'
    )
    parser.add_argument(
        '--profile',
        type=str,
        default=None,
        help='Profile to use (cusd, hoa, etc.). If not specified, uses default_profile from config.'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force reprocess all emails, ignoring tracking'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics and exit'
    )

    args = parser.parse_args()

    try:
        summarizer = CUSDSummarizer(config_path=args.config, profile=args.profile)
        
        if args.stats:
            # Just show stats
            stats = summarizer.get_stats()
            print("\n=== CUSD Summarizer Statistics ===")
            print(json.dumps(stats, indent=2))
            return
        
        # Run the summarizer
        results = summarizer.run(force_reprocess=args.force)
        
        # Print results
        print("\n=== Execution Results ===")
        print(json.dumps(results, indent=2, default=str))
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        raise
    finally:
        if 'summarizer' in locals():
            summarizer.cleanup()


if __name__ == '__main__':
    main()
