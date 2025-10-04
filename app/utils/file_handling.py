import os
from fastapi import UploadFile, HTTPException
from typing import List
import mimetypes

# Try to import magic, fallback to mimetypes
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    import mimetypes

ALLOWED_EXTENSIONS = {
    'document': ['.pdf', '.doc', '.docx', '.txt', '.ppt', '.pptx'],
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],
    'video': ['.mp4', '.avi', '.mov', '.wmv']
}

ALLOWED_MIME_TYPES = {
    'text/plain', 'application/pdf', 'image/jpeg', 'image/png', 'image/gif',
    'image/bmp', 'image/tiff', 'application/msword', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

def save_upload_file(upload_file: UploadFile, upload_dir: str = "app/temp_uploads") -> str:
    """Save uploaded file to temporary storage"""
    try:
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, upload_file.filename)
        
        with open(file_path, "wb") as buffer:
            content = upload_file.file.read()
            buffer.write(content)
        
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload error: {str(e)}")

def validate_file_type(file: UploadFile, allowed_types: List[str]) -> bool:
    """Validate file type with fallback methods"""
    try:
        # Read first 2048 bytes for detection
        content = file.file.read(2048)
        file.file.seek(0)  # Reset file pointer
        
        # Method 1: Use python-magic if available
        if HAS_MAGIC:
            mime = magic.Magic(mime=True)
            file_type = mime.from_buffer(content)
            return any(file_type.startswith(allowed) for allowed in allowed_types)
        
        # Method 2: Use filename extension as fallback
        filename = file.filename.lower()
        valid_extensions = []
        for category in allowed_types:
            if category == 'text/':
                valid_extensions.extend(['.txt', '.pdf', '.doc', '.docx'])
            elif category == 'image/':
                valid_extensions.extend(['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'])
            elif category == 'application/pdf':
                valid_extensions.append('.pdf')
        
        file_extension = os.path.splitext(filename)[1]
        return file_extension in valid_extensions
        
    except Exception:
        # Final fallback: check filename extension
        filename = file.filename.lower()
        if any(filename.endswith(ext) for ext in ['.pdf', '.txt', '.doc', '.docx', '.jpg', '.jpeg', '.png']):
            return True
        return False

def cleanup_file(file_path: str):
    """Clean up temporary file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass  # Silent cleanup

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return os.path.splitext(filename)[1].lower()

def is_allowed_extension(filename: str, category: str) -> bool:
    """Check if file extension is allowed for category"""
    extension = get_file_extension(filename)
    return extension in ALLOWED_EXTENSIONS.get(category, [])