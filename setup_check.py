#!/usr/bin/env python3
"""
Setup script for CUSD Email Summarizer
Guides user through initial configuration
"""
import os
import sys
from pathlib import Path
import json


def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def check_python_version():
    """Check if Python version is adequate."""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python version: {sys.version.split()[0]}")


def check_dependencies():
    """Check if required packages are installed."""
    required = [
        'google.auth',
        'google_auth_oauthlib',
        'googleapiclient',
        'anthropic',
        'docx',
        'PIL'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print("\n⚠️  Missing dependencies detected!")
        print("   Install with: pip install -r requirements.txt")
        return False
    
    return True


def check_api_key():
    """Check if Anthropic API key is set."""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set")
        print("\n   Set it with:")
        print("   PowerShell: [System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'your-key', 'User')")
        print("   CMD: setx ANTHROPIC_API_KEY \"your-key\"")
        return False
    
    print(f"✓ ANTHROPIC_API_KEY is set ({api_key[:8]}...)")
    return True


def check_gmail_credentials():
    """Check if Gmail OAuth credentials exist."""
    creds_path = Path(__file__).parent / 'config' / 'credentials.json'
    
    if not creds_path.exists():
        print(f"❌ Gmail credentials not found at: {creds_path}")
        print("\n   Get OAuth credentials:")
        print("   1. Go to https://console.cloud.google.com/")
        print("   2. Create/select a project")
        print("   3. Enable Gmail API")
        print("   4. Create OAuth 2.0 credentials (Desktop app)")
        print("   5. Download and save as config/credentials.json")
        return False
    
    print(f"✓ Gmail credentials found at: {creds_path}")
    return True


def check_config():
    """Check if config.json is properly configured."""
    config_path = Path(__file__).parent / 'config' / 'config.json'
    
    if not config_path.exists():
        print(f"❌ Config file not found at: {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check critical settings
        email = config.get('email', {}).get('recipient')
        if not email or email == 'erickrhoan@gmail.com':
            print("⚠️  Email recipient not configured in config.json")
            print(f"   Edit: {config_path}")
            print("   Set 'email' -> 'recipient' to your email address")
            return False
        
        print(f"✓ Config file valid")
        print(f"   Recipient: {email}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Config file has JSON errors: {e}")
        return False


def create_directories():
    """Create necessary directories."""
    base_path = Path(__file__).parent
    dirs = ['data', 'output', 'logs', 'config']
    
    for dir_name in dirs:
        dir_path = base_path / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"✓ Directory: {dir_path}")


def main():
    """Main setup routine."""
    print_header("CUSD Email Summarizer - Setup Check")
    
    print("\n1. Python Version")
    print("-" * 60)
    check_python_version()
    
    print("\n2. Dependencies")
    print("-" * 60)
    deps_ok = check_dependencies()
    
    print("\n3. API Configuration")
    print("-" * 60)
    api_ok = check_api_key()
    
    print("\n4. Gmail OAuth Credentials")
    print("-" * 60)
    gmail_ok = check_gmail_credentials()
    
    print("\n5. Configuration File")
    print("-" * 60)
    config_ok = check_config()
    
    print("\n6. Directories")
    print("-" * 60)
    create_directories()
    
    # Summary
    print_header("Setup Summary")
    
    all_ok = deps_ok and api_ok and gmail_ok and config_ok
    
    if all_ok:
        print("✅ All checks passed!")
        print("\nYou're ready to run the summarizer:")
        print("   python main.py")
        print("\nFirst run will:")
        print("   1. Open browser for Gmail OAuth")
        print("   2. Process recent CUSD emails")
        print("   3. Generate your first digest")
    else:
        print("❌ Some checks failed")
        print("\nPlease fix the issues above before running.")
        print("\nFor detailed setup instructions, see:")
        print("   README.md")
    
    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    main()
