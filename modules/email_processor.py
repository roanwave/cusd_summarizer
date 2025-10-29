"""Email content processing for CUSD Email Summarizer."""
import base64
import re
from email import message_from_bytes
from email.message import EmailMessage
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import io

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        PdfReader = None

from .logger import get_logger

logger = get_logger('email_processor')


class EmailContent:
    """Structured email content."""
    
    def __init__(
        self,
        message_id: str,
        thread_id: str,
        subject: str,
        sender: str,
        date: str,
        text_body: str = "",
        html_body: str = "",
        images: List[Dict[str, Any]] = None,
        attachments: List[Dict[str, Any]] = None
    ):
        self.message_id = message_id
        self.thread_id = thread_id
        self.subject = subject
        self.sender = sender
        self.date = date
        self.text_body = text_body
        self.html_body = html_body
        self.images = images or []
        self.attachments = attachments or []
    
    def get_body(self) -> str:
        """Get best available body content (prefer HTML, fallback to text)."""
        return self.html_body if self.html_body else self.text_body
    
    def has_images(self) -> bool:
        """Check if email has any images."""
        return len(self.images) > 0
    
    def has_attachments(self) -> bool:
        """Check if email has any attachments."""
        return len(self.attachments) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'message_id': self.message_id,
            'thread_id': self.thread_id,
            'subject': self.subject,
            'sender': self.sender,
            'date': self.date,
            'text_body': self.text_body,
            'html_body': self.html_body,
            'images': self.images,
            'attachments': self.attachments
        }


class EmailProcessor:
    """Process Gmail API messages and extract content."""

    def __init__(
        self,
        gmail_client=None,
        max_image_size_mb: int = 5,
        min_image_width: int = 150,
        min_image_height: int = 150,
        process_pdfs: bool = False
    ):
        """Initialize email processor.

        Args:
            gmail_client: GmailClient instance for downloading attachments.
            max_image_size_mb: Maximum image size to process in MB.
            min_image_width: Minimum image width in pixels (filters out small images/logos).
            min_image_height: Minimum image height in pixels (filters out small images/logos).
            process_pdfs: Whether to download and extract text from PDF attachments.
        """
        self.gmail_client = gmail_client
        self.max_image_size = max_image_size_mb * 1024 * 1024  # Convert to bytes
        self.min_image_width = min_image_width
        self.min_image_height = min_image_height
        self.process_pdfs = process_pdfs
    
    def process_message(self, gmail_message: Dict[str, Any]) -> EmailContent:
        """Process a Gmail API message and extract content.
        
        Args:
            gmail_message: Message dict from Gmail API.
            
        Returns:
            EmailContent object with extracted data.
        """
        message_id = gmail_message['id']
        thread_id = gmail_message.get('threadId', message_id)
        
        # Extract headers
        headers = self._extract_headers(gmail_message)
        
        # Extract body, images, and attachments
        text_body, html_body, images, attachments = self._extract_parts(gmail_message)
        
        # Resolve inline images (cid: references)
        if html_body and images:
            html_body = self._resolve_inline_images(html_body, images)
        
        content = EmailContent(
            message_id=message_id,
            thread_id=thread_id,
            subject=headers.get('Subject', 'No Subject'),
            sender=headers.get('From', 'Unknown'),
            date=headers.get('Date', ''),
            text_body=text_body,
            html_body=html_body,
            images=images,
            attachments=attachments
        )
        
        logger.info(
            f"Processed message {message_id}: "
            f"{len(text_body)} text chars, "
            f"{len(html_body)} html chars, "
            f"{len(images)} images, "
            f"{len(attachments)} attachments"
        )
        
        return content
    
    def _extract_headers(self, gmail_message: Dict[str, Any]) -> Dict[str, str]:
        """Extract email headers.
        
        Args:
            gmail_message: Message dict from Gmail API.
            
        Returns:
            Dictionary of header name -> value.
        """
        headers = {}
        payload = gmail_message.get('payload', {})
        
        for header in payload.get('headers', []):
            headers[header['name']] = header['value']
        
        return headers
    
    def _extract_parts(
        self,
        gmail_message: Dict[str, Any]
    ) -> Tuple[str, str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Extract text body, HTML body, images, and attachments from message.
        
        Args:
            gmail_message: Message dict from Gmail API.
            
        Returns:
            Tuple of (text_body, html_body, images_list, attachments_list).
        """
        text_body = ""
        html_body = ""
        images = []
        attachments = []
        
        payload = gmail_message.get('payload', {})
        
        # Handle single-part messages
        if 'body' in payload and payload.get('body', {}).get('data'):
            mime_type = payload.get('mimeType', '')
            body_data = payload['body']['data']
            content = self._decode_base64(body_data)
            
            if mime_type == 'text/plain':
                text_body = content
            elif mime_type == 'text/html':
                html_body = content
        
        # Handle multi-part messages
        if 'parts' in payload:
            text_body, html_body, images, attachments = self._extract_from_parts(
                payload['parts'], gmail_message['id']
            )
        
        return text_body, html_body, images, attachments
    
    def _extract_from_parts(
        self,
        parts: List[Dict[str, Any]],
        message_id: str,
        images: List[Dict[str, Any]] = None,
        attachments: List[Dict[str, Any]] = None
    ) -> Tuple[str, str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Recursively extract content from message parts.
        
        Args:
            parts: List of message parts.
            message_id: Gmail message ID (for attachment fetching).
            images: Accumulated images list.
            attachments: Accumulated attachments list.
            
        Returns:
            Tuple of (text_body, html_body, images_list, attachments_list).
        """
        if images is None:
            images = []
        if attachments is None:
            attachments = []
        
        text_body = ""
        html_body = ""
        
        for part in parts:
            mime_type = part.get('mimeType', '')
            
            # Recurse into nested parts
            if 'parts' in part:
                sub_text, sub_html, images, attachments = self._extract_from_parts(
                    part['parts'], message_id, images, attachments
                )
                text_body += sub_text
                html_body += sub_html
                continue
            
            # Extract body content
            if 'body' in part and part['body'].get('data'):
                content = self._decode_base64(part['body']['data'])
                
                if mime_type == 'text/plain':
                    text_body += content
                elif mime_type == 'text/html':
                    html_body += content
            
            # Extract images
            if mime_type.startswith('image/'):
                image_data = self._extract_image(part)
                if image_data:
                    images.append(image_data)
            
            # Detect PDF attachments
            elif mime_type == 'application/pdf':
                attachment_info = self._extract_attachment_info(part, message_id)
                if attachment_info:
                    # Download and extract text if configured
                    if self.process_pdfs and self.gmail_client and PdfReader:
                        pdf_text = self._extract_pdf_text(
                            message_id,
                            attachment_info['attachment_id']
                        )
                        if pdf_text:
                            attachment_info['extracted_text'] = pdf_text
                    attachments.append(attachment_info)
        
        return text_body, html_body, images, attachments
    
    def _extract_attachment_info(
        self,
        part: Dict[str, Any],
        message_id: str
    ) -> Optional[Dict[str, Any]]:
        """Extract attachment metadata (for PDF attachments).
        
        Args:
            part: Message part dict.
            message_id: Gmail message ID.
            
        Returns:
            Attachment info dict or None.
        """
        try:
            filename = part.get('filename', 'attachment.pdf')
            mime_type = part.get('mimeType', 'application/pdf')
            body = part.get('body', {})
            
            if 'attachmentId' not in body:
                return None
            
            logger.info(f"Found PDF attachment: {filename}")
            
            return {
                'filename': filename,
                'mime_type': mime_type,
                'attachment_id': body['attachmentId'],
                'size': body.get('size', 0),
                'message_id': message_id
            }
            
        except Exception as e:
            logger.error(f"Error extracting attachment info: {e}")
            return None
    
    def _extract_image(self, part: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract image data from message part.
        
        Args:
            part: Message part dict.
            
        Returns:
            Image data dict or None if extraction fails.
        """
        try:
            filename = part.get('filename', 'image')
            mime_type = part.get('mimeType', 'image/png')
            
            # Get content ID for inline images
            content_id = None
            for header in part.get('headers', []):
                if header['name'].lower() == 'content-id':
                    content_id = header['value'].strip('<>')
                    break
            
            # Get image data
            body = part.get('body', {})
            if 'attachmentId' in body:
                # Attachment - would need separate API call to fetch
                logger.debug(f"Skipping attachment image: {filename}")
                return None
            
            if not body.get('data'):
                return None
            
            data = self._decode_base64(body['data'])

            # Check size
            if len(data) > self.max_image_size:
                logger.warning(
                    f"Image {filename} too large ({len(data)} bytes), skipping"
                )
                return None

            # Validate image and check dimensions if PIL is available
            img_width = None
            img_height = None

            if Image:
                try:
                    img = Image.open(io.BytesIO(data))
                    img_width, img_height = img.size

                    # Filter out small images (signatures, logos, decorative graphics)
                    if img_width < self.min_image_width or img_height < self.min_image_height:
                        logger.info(
                            f"Image {filename} too small ({img_width}x{img_height}), "
                            f"likely signature/logo - skipping"
                        )
                        return None

                    # Verify image integrity
                    img.verify()
                    logger.debug(
                        f"Validated image: {filename} ({img.format}, {img_width}x{img_height})"
                    )
                except Exception as e:
                    logger.warning(f"Invalid image {filename}: {e}")
                    return None
            
            return {
                'filename': filename,
                'mime_type': mime_type,
                'content_id': content_id,
                'data': data,
                'size': len(data),
                'width': img_width,
                'height': img_height
            }
            
        except Exception as e:
            logger.error(f"Error extracting image: {e}")
            return None
    
    def _decode_base64(self, data: str) -> str:
        """Decode base64-encoded data.
        
        Args:
            data: Base64-encoded string.
            
        Returns:
            Decoded string.
        """
        try:
            # Gmail uses URL-safe base64
            decoded = base64.urlsafe_b64decode(data)
            return decoded.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error decoding base64: {e}")
            return ""
    
    def _resolve_inline_images(
        self,
        html: str,
        images: List[Dict[str, Any]]
    ) -> str:
        """Resolve cid: image references in HTML.
        
        Args:
            html: HTML content with potential cid: references.
            images: List of image dicts with content_id.
            
        Returns:
            HTML with cid: references resolved to data URIs.
        """
        # Create mapping of content_id -> image data
        cid_map = {}
        for img in images:
            if img.get('content_id'):
                cid_map[img['content_id']] = img
        
        # Replace cid: references with data URIs
        def replace_cid(match):
            cid = match.group(1)
            if cid in cid_map:
                img = cid_map[cid]
                data_b64 = base64.b64encode(img['data']).decode('utf-8')
                return f'src="data:{img["mime_type"]};base64,{data_b64}"'
            return match.group(0)
        
        html = re.sub(r'src="cid:([^"]+)"', replace_cid, html)
        
        return html
    
    def _extract_pdf_text(
        self,
        message_id: str,
        attachment_id: str,
        max_chars: int = 10000
    ) -> Optional[str]:
        """Extract text from PDF attachment.

        Args:
            message_id: Gmail message ID.
            attachment_id: Attachment ID.
            max_chars: Maximum characters to extract (to avoid huge PDFs).

        Returns:
            Extracted text or None if extraction fails.
        """
        if not PdfReader:
            logger.warning("PDF processing not available (pypdf/PyPDF2 not installed)")
            return None

        try:
            # Download attachment
            pdf_data = self.gmail_client.get_attachment(message_id, attachment_id)
            if not pdf_data:
                logger.warning(f"Failed to download PDF attachment {attachment_id}")
                return None

            # Extract text
            pdf_file = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_file)

            text_parts = []
            total_chars = 0

            for page_num, page in enumerate(reader.pages):
                if total_chars >= max_chars:
                    logger.info(f"PDF text extraction stopped at page {page_num} (max chars reached)")
                    break

                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                        total_chars += len(page_text)
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {e}")
                    continue

            if text_parts:
                full_text = '\n\n'.join(text_parts)
                logger.info(f"Extracted {len(full_text)} characters from PDF ({len(reader.pages)} pages)")
                return full_text[:max_chars]  # Ensure we don't exceed limit

            return None

        except Exception as e:
            logger.error(f"Error processing PDF attachment {attachment_id}: {e}")
            return None

    def save_image(self, image_data: Dict[str, Any], output_dir: Path) -> Path:
        """Save image data to file.

        Args:
            image_data: Image dict with 'data' and 'filename'.
            output_dir: Directory to save image.

        Returns:
            Path to saved image file.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filepath = output_dir / image_data['filename']

        # Ensure unique filename
        counter = 1
        while filepath.exists():
            name = Path(image_data['filename']).stem
            ext = Path(image_data['filename']).suffix
            filepath = output_dir / f"{name}_{counter}{ext}"
            counter += 1

        with open(filepath, 'wb') as f:
            f.write(image_data['data'])

        logger.debug(f"Saved image to {filepath}")
        return filepath
