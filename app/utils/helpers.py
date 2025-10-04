import hashlib
import uuid,os
from datetime import datetime, timedelta
from typing import Any, Dict

def generate_unique_id() -> str:
    """Generate a unique ID"""
    return str(uuid.uuid4())

def hash_password(password: str) -> str:
    """Hash a password (basic implementation - use proper hashing in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display"""
    try:
        # Handle different timestamp formats from YouTube
        if '.' in timestamp:
            parts = timestamp.split('.')
            return parts[0]  # Return only seconds part
        return timestamp
    except:
        return timestamp

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove unsafe characters"""
    import re
    # Remove characters that are not safe for filenames
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(sanitized) > 100:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:95] + ext
    return sanitized

def chunk_text(text: str, max_length: int = 4000) -> list:
    """Split text into chunks for processing"""
    chunks = []
    words = text.split()
    current_chunk = []
    
    for word in words:
        if len(' '.join(current_chunk + [word])) <= max_length:
            current_chunk.append(word)
        else:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def calculate_processing_time(start_time: datetime) -> float:
    """Calculate processing time in seconds"""
    return (datetime.now() - start_time).total_seconds()