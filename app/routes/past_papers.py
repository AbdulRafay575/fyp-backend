from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBearer
from typing import Optional
import os

from app.services.document_service import DocumentService
from app.services.ocr_service import OCRService
from app.services.chatgpt_service import ChatGPTService
from app.services.auth_service import AuthService
from app.utils.file_handling import save_upload_file, cleanup_file, validate_file_type

router = APIRouter()
document_service = DocumentService()
ocr_service = OCRService()
chatgpt_service = ChatGPTService()
auth_service = AuthService()
security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    """Dependency to get current user"""
    try:
        user = auth_service.get_current_user(token.credentials)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")

@router.post("/analyze")
async def analyze_past_papers(
    study_material_file: UploadFile = File(...),
    past_paper_file: UploadFile = File(...),
    num_questions: int = 10,
    user = Depends(get_current_user)
):
    """Analyze past papers and generate questions based on patterns"""
    try:
        user_id = user["user"]["id"]
        
        print(f"Past paper analysis for user: {user_id}")
        
        # Validate files
        if not validate_file_type(study_material_file, ['text/', 'application/pdf', 'image/']):
            raise HTTPException(status_code=400, detail="Invalid study material file type")
        if not validate_file_type(past_paper_file, ['text/', 'application/pdf', 'image/']):
            raise HTTPException(status_code=400, detail="Invalid past paper file type")
        
        # Save files
        study_material_path = save_upload_file(study_material_file)
        past_paper_path = save_upload_file(past_paper_file)
        
        try:
            # Extract text from study material (with chunking for large files)
            print("Extracting text from study material...")
            if study_material_file.content_type.startswith('image/'):
                study_material_text = ocr_service.extract_text_from_image(study_material_path)
            else:
                study_material_text = document_service.extract_text(study_material_path)
            
            print(f"Study material text length: {len(study_material_text)}")
            
            # Extract text from past paper (usually smaller)
            print("Extracting text from past paper...")
            if past_paper_file.content_type.startswith('image/'):
                past_paper_text = ocr_service.extract_text_from_image(past_paper_path)
            else:
                past_paper_text = document_service.extract_text(past_paper_path)
            
            print(f"Past paper text length: {len(past_paper_text)}")
            
            # Handle large study materials with chunking
            if len(study_material_text) > 8000:
                print("Large study material detected, using chunked processing...")
                study_chunks = document_service.extract_text_chunked(study_material_path)
                # Use first few chunks for analysis (most important content)
                study_material_text = " ".join(study_chunks[:5])
                print(f"Using first {len(study_chunks[:5])} chunks of study material")
            
            # Analyze with ChatGPT
            print("Analyzing with ChatGPT...")
            analysis_result = chatgpt_service.analyze_past_papers(
                study_material_text, 
                past_paper_text, 
                num_questions
            )
            
            # Parse the response
            parsed_result = parse_past_paper_analysis(analysis_result)
            
            return {
                "success": True,
                "study_material_filename": study_material_file.filename,
                "past_paper_filename": past_paper_file.filename,
                "analysis": parsed_result,
                "study_material_length": len(study_material_text),
                "past_paper_length": len(past_paper_text)
            }
            
        except Exception as e:
            print(f"Error in past paper analysis: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
            
        finally:
            cleanup_file(study_material_path)
            cleanup_file(past_paper_path)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Past paper analysis endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def parse_past_paper_analysis(analysis_text: str) -> dict:
    """Parse the past paper analysis response into structured format"""
    try:
        lines = analysis_text.split('\n')
        sections = {
            "analysis": "",
            "questions": [],
            "answers": [],
            "full_text": analysis_text
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if "ANALYSIS:" in line:
                current_section = "analysis"
                sections["analysis"] = line.replace("ANALYSIS:", "").strip()
            elif "QUESTIONS:" in line:
                current_section = "questions"
            elif "ANSWERS:" in line:
                current_section = "answers"
            elif current_section == "analysis" and not line.startswith("QUESTIONS:"):
                sections["analysis"] += " " + line
            elif current_section == "questions" and not line.startswith("ANSWERS:"):
                if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                    question = line.lstrip("1234567890.-• ").strip()
                    if question and not question.startswith("QUESTIONS:"):
                        sections["questions"].append(question)
            elif current_section == "answers" and line:
                if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                    answer = line.lstrip("1234567890.-• ").strip()
                    if answer and not answer.startswith("ANSWERS:"):
                        sections["answers"].append(answer)
        
        # Clean up analysis
        sections["analysis"] = sections["analysis"].strip()
        
        # Ensure we have matching questions and answers
        min_length = min(len(sections["questions"]), len(sections["answers"]))
        sections["questions"] = sections["questions"][:min_length]
        sections["answers"] = sections["answers"][:min_length]
        
        return sections
        
    except Exception as e:
        print(f"Error parsing past paper analysis: {str(e)}")
        # Fallback if parsing fails
        return {
            "analysis": "Analysis parsing failed",
            "questions": ["Question parsing failed"],
            "answers": ["Answer parsing failed"],
            "full_text": analysis_text
        }