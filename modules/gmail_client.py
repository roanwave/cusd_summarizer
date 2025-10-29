"""Gmail API integration for CUSD Email Summarizer."""
import base64
import os
import pickle
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Dict, Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .logger import get_logger

logger = get_logger('gmail')


class GmailClient:
    """Gmail API client for retrieving and sending emails."""
    
    def __init__(self, credentials_file: str, token_file: str, scopes: List[str]):
        """Initialize Gmail client.
        
        Args:
            credentials_file: Path to OAuth credentials JSON file.
            token_file: Path to store/load access token.
            scopes: List of Gmail API scopes to request.
        """
        self.credentials_file = Path(credentials_file)
        self.token_file = Path(token_file)
        self.scopes = scopes
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API using OAuth 2.0."""
        creds = None
        
        # Load existing token if available
        if self.token_file.exists():
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                if not self.credentials_file.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}\n"
                        f"Please download OAuth credentials from Google Cloud Console."
                    )
                
                logger.info("Starting OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_file), self.scopes
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
            logger.info(f"Credentials saved to {self.token_file}")
        
        # Build service
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail API authenticated successfully")
    
    def get_label_id(self, label_name: str) -> Optional[str]:
        """Get Gmail label ID by name.
        
        Args:
            label_name: Name of the label to find.
            
        Returns:
            Label ID if found, None otherwise.
        """
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            for label in labels:
                if label['name'].upper() == label_name.upper():
                    return label['id']
            
            logger.warning(f"Label '{label_name}' not found")
            return None
            
        except HttpError as error:
            logger.error(f"Error fetching labels: {error}")
            return None
    
    def list_messages(
        self,
        label_name: str,
        lookback_hours: int = 48,
        exclude_ids: List[str] = None
    ) -> List[Dict[str, Any]]:
        """List messages with specified label within time range.
        
        Args:
            label_name: Gmail label name to filter by.
            lookback_hours: Hours to look back from now.
            exclude_ids: List of message IDs to exclude.
            
        Returns:
            List of message metadata dictionaries.
        """
        label_id = self.get_label_id(label_name)
        if not label_id:
            logger.error(f"Cannot list messages: label '{label_name}' not found")
            return []
        
        # Calculate date filter
        cutoff_date = datetime.now() - timedelta(hours=lookback_hours)
        date_str = cutoff_date.strftime('%Y/%m/%d')
        
        # Build query
        query = f'label:{label_name} after:{date_str}'
        
        try:
            messages = []
            page_token = None
            
            while True:
                results = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    pageToken=page_token
                ).execute()
                
                batch = results.get('messages', [])
                messages.extend(batch)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            logger.info(f"Found {len(messages)} messages with label '{label_name}'")
            
            # Filter out excluded IDs
            if exclude_ids:
                messages = [m for m in messages if m['id'] not in exclude_ids]
                logger.info(f"{len(messages)} messages after excluding processed IDs")
            
            return messages
            
        except HttpError as error:
            logger.error(f"Error listing messages: {error}")
            return []
    
    def get_message(self, message_id: str, format: str = 'full') -> Optional[Dict[str, Any]]:
        """Get full message details by ID.
        
        Args:
            message_id: Gmail message ID.
            format: Message format (minimal, full, raw, metadata).
            
        Returns:
            Message dictionary or None if error.
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format=format
            ).execute()
            
            return message
            
        except HttpError as error:
            logger.error(f"Error fetching message {message_id}: {error}")
            return None
    
    def get_attachment(self, message_id: str, attachment_id: str) -> Optional[bytes]:
        """Get attachment data by ID.
        
        Args:
            message_id: Gmail message ID.
            attachment_id: Attachment ID from message part.
            
        Returns:
            Attachment data as bytes or None if error.
        """
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            data = attachment.get('data')
            if data:
                return base64.urlsafe_b64decode(data)
            
            return None
            
        except HttpError as error:
            logger.error(f"Error fetching attachment {attachment_id}: {error}")
            return None
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachment_path: str = None
    ) -> bool:
        """Send an email via Gmail API.
        
        Args:
            to: Recipient email address.
            subject: Email subject.
            body: Email body (plain text).
            attachment_path: Optional path to file to attach.
            
        Returns:
            True if sent successfully, False otherwise.
        """
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            # TODO: Add attachment handling if needed
            if attachment_path:
                logger.warning("Attachment handling not yet implemented")
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            # Send
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent successfully to {to}")
            return True
            
        except HttpError as error:
            logger.error(f"Error sending email: {error}")
            return False
    
    def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user's Gmail profile.
        
        Returns:
            Profile dictionary with emailAddress, messagesTotal, etc.
        """
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return profile
        except HttpError as error:
            logger.error(f"Error fetching profile: {error}")
            return None
