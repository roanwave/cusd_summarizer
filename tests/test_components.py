#!/usr/bin/env python3
"""
Basic tests for CUSD Email Summarizer components
"""
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent / 'modules'))

def test_config():
    """Test configuration loading."""
    print("Testing configuration...")
    try:
        from modules.config_manager import get_config
        config = get_config()
        
        assert config.get('gmail', 'label') == 'CUSD'
        assert config.get('ai', 'provider') == 'anthropic'
        
        print("✓ Config loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False


def test_logger():
    """Test logging setup."""
    print("\nTesting logger...")
    try:
        from modules.logger import setup_logging, get_logger
        
        logger = setup_logging(
            log_level="INFO",
            console_output=False
        )
        
        logger.info("Test log message")
        print("✓ Logger working")
        return True
    except Exception as e:
        print(f"❌ Logger test failed: {e}")
        return False


def test_email_processor():
    """Test email processor."""
    print("\nTesting email processor...")
    try:
        from modules.email_processor import EmailProcessor, EmailContent
        
        processor = EmailProcessor()
        
        # Create test email content
        email = EmailContent(
            message_id="test123",
            thread_id="test123",
            subject="Test Email",
            sender="test@example.com",
            date="2025-10-13",
            text_body="This is a test email"
        )
        
        assert email.get_body() == "This is a test email"
        assert not email.has_images()
        
        print("✓ Email processor working")
        return True
    except Exception as e:
        print(f"❌ Email processor test failed: {e}")
        return False


def test_tracker():
    """Test email tracker."""
    print("\nTesting tracker...")
    try:
        from modules.tracker import EmailTracker
        import tempfile
        
        # Use temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        tracker = EmailTracker(db_path)
        
        # Test marking as processed
        tracker.mark_processed(
            message_id="test123",
            thread_id="test123",
            subject="Test",
            sender="test@example.com"
        )
        
        # Test checking if processed
        assert tracker.is_processed("test123")
        assert not tracker.is_processed("nonexistent")
        
        # Test getting stats
        stats = tracker.get_stats()
        assert stats['total_processed_emails'] == 1
        
        tracker.close()
        
        # Cleanup
        Path(db_path).unlink()
        
        print("✓ Tracker working")
        return True
    except Exception as e:
        print(f"❌ Tracker test failed: {e}")
        return False


def test_document_generator():
    """Test document generator."""
    print("\nTesting document generator...")
    try:
        from modules.document_generator import DocumentGenerator
        import tempfile
        
        # Use temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            generator = DocumentGenerator(tmp_dir)
            
            # Test data
            digest_data = {
                'executive_summary': 'Test summary',
                'event_calendar': [
                    {
                        'title': 'Test Event',
                        'date': '2025-10-15',
                        'time': '10:00 AM',
                        'location': 'School'
                    }
                ],
                'action_items': [
                    {
                        'action': 'Sign permission slip',
                        'deadline': '2025-10-14',
                        'priority': 'high'
                    }
                ]
            }
            
            email_summaries = [
                {
                    'subject': 'Test Email',
                    'sender': 'test@example.com',
                    'date': '2025-10-13',
                    'summary': 'Test summary',
                    'importance': 'medium',
                    'events': [],
                    'action_items': []
                }
            ]
            
            # Generate document
            doc_path = generator.create_digest_document(
                digest_data=digest_data,
                email_summaries=email_summaries,
                date_str="October 13, 2025"
            )
            
            assert doc_path.exists()
            assert doc_path.suffix == '.docx'
        
        print("✓ Document generator working")
        return True
    except Exception as e:
        print(f"❌ Document generator test failed: {e}")
        return False


def test_api_key():
    """Test API key availability."""
    print("\nTesting API key...")
    try:
        from modules.config_manager import get_config
        config = get_config()
        api_key = config.get_ai_api_key()
        
        assert api_key, "API key not found"
        assert api_key.startswith('sk-'), "Invalid API key format"
        
        print(f"✓ API key found ({api_key[:8]}...)")
        return True
    except Exception as e:
        print(f"❌ API key test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("CUSD Email Summarizer - Component Tests")
    print("="*60)
    
    tests = [
        test_config,
        test_logger,
        test_email_processor,
        test_tracker,
        test_document_generator,
        test_api_key
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    
    print("="*60 + "\n")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
