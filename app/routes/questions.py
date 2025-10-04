from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBearer
from app.services.ocr_service import OCRService
from app.services.chatgpt_service import ChatGPTService
from app.services.auth_service import AuthService
from app.utils.file_handling import save_upload_file, cleanup_file, validate_file_type

router = APIRouter()
ocr_service = OCRService()
chatgpt_service = ChatGPTService()
auth_service = AuthService()
security = HTTPBearer()

@router.post("/generate")
async def generate_questions(
    file: UploadFile = File(None),
    text: str = None,
    token: str = Depends(security)
):
    """Generate questions from document or text"""
    try:
        user = auth_service.get_current_user(token)
        
        if not file and not text:
            raise HTTPException(status_code=400, detail="Either file or text must be provided")
        
        extracted_text = ""
        
        if file:
            # Validate file type
            if not validate_file_type(file, ['text/', 'application/pdf', 'image/']):
                raise HTTPException(status_code=400, detail="Invalid file type")
            
            file_path = save_upload_file(file)
            
            try:
                if file.content_type.startswith('image/'):
                    extracted_text = ocr_service.extract_text_from_image(file_path)
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        extracted_text = f.read()
            finally:
                cleanup_file(file_path)
        else:
            extracted_text = text
        
        # Generate questions using ChatGPT
        questions = chatgpt_service.generate_questions(extracted_text)
        
        return {
            "success": True,
            "questions": questions,
            "input_length": len(extracted_text)
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



