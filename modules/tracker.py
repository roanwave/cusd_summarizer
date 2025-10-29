"""Email tracking database for CUSD Email Summarizer."""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

from .logger import get_logger

logger = get_logger('tracker')


class EmailTracker:
    """Track processed emails to prevent duplicates."""
    
    def __init__(self, db_path: str):
        """Initialize email tracker.
        
        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database and create tables."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Return rows as dicts
        
        cursor = self.conn.cursor()
        
        # Create processed_emails table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_emails (
                message_id TEXT PRIMARY KEY,
                thread_id TEXT,
                subject TEXT,
                sender TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                summary TEXT
            )
        """)
        
        # Create digests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS digests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                email_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                digest_file TEXT,
                digest_data TEXT
            )
        """)
        
        # Create index on processed_at for faster cleanup queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_processed_at 
            ON processed_emails(processed_at)
        """)
        
        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")
    
    def is_processed(self, message_id: str) -> bool:
        """Check if a message has already been processed.
        
        Args:
            message_id: Gmail message ID.
            
        Returns:
            True if message has been processed, False otherwise.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM processed_emails WHERE message_id = ?",
            (message_id,)
        )
        return cursor.fetchone() is not None
    
    def mark_processed(
        self,
        message_id: str,
        thread_id: str,
        subject: str,
        sender: str,
        summary: str = None
    ):
        """Mark a message as processed.
        
        Args:
            message_id: Gmail message ID.
            thread_id: Gmail thread ID.
            subject: Email subject.
            sender: Email sender.
            summary: Summary data (can be dict or JSON string).
        """
        # If summary is a dict, convert to JSON string for storage
        if isinstance(summary, dict):
            summary = json.dumps(summary)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO processed_emails 
            (message_id, thread_id, subject, sender, summary)
            VALUES (?, ?, ?, ?, ?)
        """, (message_id, thread_id, subject, sender, summary))
        
        self.conn.commit()
        logger.debug(f"Marked message {message_id} as processed")
    
    def get_processed_ids(self, since_days: int = 7) -> List[str]:
        """Get list of processed message IDs from recent period.
        
        Args:
            since_days: Number of days to look back.
            
        Returns:
            List of message IDs.
        """
        cursor = self.conn.cursor()
        cutoff = datetime.now() - timedelta(days=since_days)
        
        cursor.execute("""
            SELECT message_id FROM processed_emails
            WHERE processed_at >= ?
        """, (cutoff,))
        
        return [row['message_id'] for row in cursor.fetchall()]
    
    def get_all_processed_ids(self) -> List[str]:
        """Get all processed message IDs regardless of age.
        
        Returns:
            List of all message IDs.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT message_id FROM processed_emails")
        return [row['message_id'] for row in cursor.fetchall()]
    
    def get_email_summaries(self, since_days: int = 14) -> List[Dict[str, Any]]:
        """Get summaries for recent processed emails.
        
        Args:
            since_days: Number of days to look back.
            
        Returns:
            List of summary dictionaries.
        """
        cursor = self.conn.cursor()
        cutoff = datetime.now() - timedelta(days=since_days)
        
        cursor.execute("""
            SELECT message_id, thread_id, subject, sender, summary, processed_at
            FROM processed_emails
            WHERE processed_at >= ?
            ORDER BY processed_at DESC
        """, (cutoff,))
        
        summaries = []
        for row in cursor.fetchall():
            summary_data = dict(row)
            
            # Parse JSON summary back to dict if it exists
            if summary_data.get('summary'):
                try:
                    summary_data['summary'] = json.loads(summary_data['summary'])
                except (json.JSONDecodeError, TypeError):
                    # If it's not valid JSON, keep as string
                    pass
            
            summaries.append(summary_data)
        
        return summaries
    
    def save_digest(
        self,
        date: str,
        email_count: int,
        digest_file: str,
        digest_data: Dict[str, Any]
    ):
        """Save digest metadata.
        
        Args:
            date: Digest date string.
            email_count: Number of emails in digest.
            digest_file: Path to digest file.
            digest_data: Digest content dictionary.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO digests (date, email_count, digest_file, digest_data)
            VALUES (?, ?, ?, ?)
        """, (date, email_count, digest_file, json.dumps(digest_data)))
        
        self.conn.commit()
        logger.info(f"Saved digest for {date}")
    
    def get_recent_digests(self, count: int = 7) -> List[Dict[str, Any]]:
        """Get recent digest records.
        
        Args:
            count: Number of recent digests to retrieve.
            
        Returns:
            List of digest dictionaries.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM digests
            ORDER BY created_at DESC
            LIMIT ?
        """, (count,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_records(self, retention_days: int = 30):
        """Delete old processed email records.
        
        Args:
            retention_days: Number of days to retain records.
        """
        cursor = self.conn.cursor()
        cutoff = datetime.now() - timedelta(days=retention_days)
        
        cursor.execute("""
            DELETE FROM processed_emails
            WHERE processed_at < ?
        """, (cutoff,))
        
        deleted_count = cursor.rowcount
        self.conn.commit()
        
        logger.info(f"Cleaned up {deleted_count} old records")
        return deleted_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with statistics.
        """
        cursor = self.conn.cursor()
        
        # Total processed emails
        cursor.execute("SELECT COUNT(*) as count FROM processed_emails")
        total_emails = cursor.fetchone()['count']
        
        # Emails in last 7 days
        cursor.execute("""
            SELECT COUNT(*) as count FROM processed_emails
            WHERE processed_at >= datetime('now', '-7 days')
        """)
        recent_emails = cursor.fetchone()['count']
        
        # Total digests
        cursor.execute("SELECT COUNT(*) as count FROM digests")
        total_digests = cursor.fetchone()['count']
        
        # Most recent digest
        cursor.execute("""
            SELECT date, created_at FROM digests
            ORDER BY created_at DESC
            LIMIT 1
        """)
        recent_digest = cursor.fetchone()
        
        return {
            'total_processed_emails': total_emails,
            'emails_last_7_days': recent_emails,
            'total_digests': total_digests,
            'most_recent_digest': dict(recent_digest) if recent_digest else None
        }
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.debug("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
