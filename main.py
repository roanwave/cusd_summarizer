#!/usr/bin/env python3
"""
CUSD Email Summarizer - Main Entry Point

This script automates the process of:
1. Scanning Gmail for CUSD-labeled school emails
2. Extracting content including inline images
3. Summarizing with AI (Claude)
4. Generating a consolidated daily digest document
5. Sending the digest via email

Usage:
    python main.py                    # Normal run
    python main.py --force            # Reprocess all emails
    python main.py --stats            # Show statistics
    python main.py --config path.json # Use custom config
"""
import sys
from pathlib import Path

# Add modules directory to path
sys.path.insert(0, str(Path(__file__).parent / 'modules'))

from modules.cusd_summarizer import main

if __name__ == '__main__':
    main()
