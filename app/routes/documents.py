from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body
from fastapi.security import HTTPBearer
from typing import Optional
import os
import re
from typing import Dict, Any, List

from app.services.document_service import DocumentService
from app.services.ocr_service import OCRService
from app.services.chatgpt_service import ChatGPTService
from app.services.auth_service import AuthService
from app.services.summary_service import SummaryService
from app.utils.file_handling import save_upload_file, cleanup_file, validate_file_type

router = APIRouter()
document_service = DocumentService()
ocr_service = OCRService()
chatgpt_service = ChatGPTService()
auth_service = AuthService()
summary_service = SummaryService()
security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    """Dependency to get current user - same as YouTube routes"""
    try:
        user = auth_service.get_current_user(token.credentials)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")



@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user = Depends(get_current_user)
):
    """Upload and process document with chunked processing for large files"""
    try:
        user_id = user["user"]["id"]
        
        print(f"Processing document for user: {user_id}")
        
        # Validate file type
        if not validate_file_type(file, ['text/', 'application/pdf', 'image/']):
            raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOCX, TXT, and images are supported.")
        
        # Save uploaded file
        file_path = save_upload_file(file)
        
        try:
            # Extract text based on file type
            if file.content_type.startswith('image/'):
                print("Processing image file...")
                extracted_text = ocr_service.extract_text_from_image(file_path)
                print(f"Extracted text length: {len(extracted_text)}")
                
                # Generate summary
                summary = chatgpt_service.get_summary(extracted_text)
                
            else:
                print("Processing document file...")
                # Extract text with chunking for large documents
                full_text = document_service.extract_text(file_path)
                print(f"Extracted text length: {len(full_text)}")
                
                # Check if document is large and needs chunking
                if len(full_text) > 3000:
                    print("Large document detected, using chunked processing...")
                    text_chunks = document_service.extract_text_chunked(file_path)
                    print(f"Split into {len(text_chunks)} chunks")
                    summary = chatgpt_service.get_chunked_summary(text_chunks)
                else:
                    print("Small document, using direct processing...")
                    summary = chatgpt_service.get_summary(full_text)
            
            # Parse summary into structured format
            parsed_summary = parse_summary_response(summary)
            
            return {
                "success": True,
                "filename": file.filename,
                "summary": parsed_summary,
                "text_preview": (extracted_text if 'extracted_text' in locals() else full_text)[:500] + "..." if len(extracted_text if 'extracted_text' in locals() else full_text) > 500 else (extracted_text if 'extracted_text' in locals() else full_text),
                "full_text_length": len(extracted_text if 'extracted_text' in locals() else full_text)
            }
            
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
            
        finally:
            cleanup_file(file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/ocr")
async def ocr_text(
    file: UploadFile = File(...),
    user = Depends(get_current_user)
):
    """Clean and structure OCR-extracted text from handwritten notes"""
    try:
        user_id = user["user"]["id"]
        
        print(f"Processing document for user: {user_id}")
        
        # Validate file type
        if not validate_file_type(file, ['text/', 'application/pdf', 'image/']):
            raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOCX, TXT, and images are supported.")
        
        # Save uploaded file
        file_path = save_upload_file(file)
        
        try:
            # Extract text based on file type
            if file.content_type.startswith('image/'):
                print("Processing image file...")
                extracted_text = ocr_service.extract_text_from_image(file_path)
                print(f"Extracted text length: {len(extracted_text)}")
                
                # Generate summary
                summary = chatgpt_service.get_summary(extracted_text)
                
            else:
                print("Processing document file...")
                # Extract text with chunking for large documents
                full_text = document_service.extract_text(file_path)
                print(f"Extracted text length: {len(full_text)}")
                
                # Check if document is large and needs chunking
                if len(full_text) > 3000:
                    print("Large document detected, using chunked processing...")
                    text_chunks = document_service.extract_text_chunked(file_path)
                    print(f"Split into {len(text_chunks)} chunks")
                    summary = chatgpt_service.get_chunked_OCR(text_chunks)
                else:
                    print("Small document, using direct processing...")
                    summary = chatgpt_service.get_OCR(full_text)
            
            # Parse summary into structured format
            parsed_summary = parse_summary_response(summary)
            
            return {
                "success": True,
                "filename": file.filename,
                "summary": parsed_summary,
                "text_preview": (extracted_text if 'extracted_text' in locals() else full_text)[:500] + "..." if len(extracted_text if 'extracted_text' in locals() else full_text) > 500 else (extracted_text if 'extracted_text' in locals() else full_text),
                "full_text_length": len(extracted_text if 'extracted_text' in locals() else full_text)
            }
            
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
            
        finally:
            cleanup_file(file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-questions")
async def generate_questions_from_document(
    file: UploadFile = File(...),
    num_questions: int = 10,
    user = Depends(get_current_user)
):
    """Generate practice questions from document with chunked processing"""
    try:
        user_id = user["user"]["id"]
        
        print(f"Generating questions for user: {user_id}")
        
        # Validate file type
        if not validate_file_type(file, ['text/', 'application/pdf', 'image/']):
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        file_path = save_upload_file(file)
        
        try:
            # Extract text
            if file.content_type.startswith('image/'):
                extracted_text = ocr_service.extract_text_from_image(file_path)
            else:
                extracted_text = document_service.extract_text(file_path)
            
            print(f"Extracted text length for questions: {len(extracted_text)}")
            
            # Generate questions with chunking for large documents
            if len(extracted_text) > 4000:
                print("Large document detected, using chunked question generation...")
                text_chunks = document_service.extract_text_chunked(file_path)
                questions = chatgpt_service.generate_chunked_questions(text_chunks, num_questions)
            else:
                questions = chatgpt_service.generate_questions(extracted_text, num_questions)
            
            # Parse questions into structured format
            parsed_questions = parse_questions_response(questions)
            
            return {
                "success": True,
                "filename": file.filename,
                "questions": parsed_questions,
                "total_questions": len(parsed_questions.get("questions", []))
            }
            
        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Question generation error: {str(e)}")
            
        finally:
            cleanup_file(file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Question generation endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# NEW ENDPOINT 1: Generate questions from text input
@router.post("/generate-questions-from-text")
async def generate_questions_from_text_input(
    text_data: dict = Body(...),
    user = Depends(get_current_user)
):
    """Generate practice questions from text input (frontend text)"""
    try:
        user_id = user["user"]["id"]
        print(f"Generating questions from text input for user: {user_id}")

        # Extract text and optional number of questions from request body
        text = text_data.get("text", "")
        num_questions = text_data.get("num_questions", 10)
        
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text input is required")
        
        if num_questions < 1 or num_questions > 20:
            num_questions = 10  # Default to 10 if out of range
        
        print(f"Generating {num_questions} questions from text input (length: {len(text)})")
        
        # Use the new service method
        questions_response = chatgpt_service.generate_questions_from_text_input(text, num_questions)
        
        # Parse the response
        parsed_questions = parse_questions_response(questions_response)
        
        return {
            "success": True,
            "questions": parsed_questions,
            "total_questions": len(parsed_questions.get("questions", [])),
            "input_text_preview": text[:200] + "..." if len(text) > 200 else text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating questions from text input: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# NEW ENDPOINT 2: Answer question from uploaded document
@router.post("/answer-question-from-document")
async def answer_question_from_document(
    file: UploadFile = File(...),
    question: str = Body(...),
    user = Depends(get_current_user)
):
    """Answer a specific question based on the uploaded document content"""
    try:
        user_id = user["user"]["id"]
        print(f"Answering question from document for user: {user_id}")
        
        if not question or len(question.strip()) == 0:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Validate file type
        if not validate_file_type(file, ['text/', 'application/pdf', 'image/']):
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        file_path = save_upload_file(file)
        
        try:
            # Extract text from document
            if file.content_type.startswith('image/'):
                extracted_text = ocr_service.extract_text_from_image(file_path)
            else:
                extracted_text = document_service.extract_text(file_path)
            
            print(f"Extracted text length: {len(extracted_text)}")
            print(f"Question: {question}")
            
            # Use the new service method to answer the question
            answer_response = chatgpt_service.answer_question_from_document(extracted_text, question)
            
            # Parse the response into structured format
            parsed_answer = parse_answer_response(answer_response)
            
            return {
                "success": True,
                "filename": file.filename,
                "question": question,
                "answer": parsed_answer,
                "document_preview": extracted_text[:300] + "..." if len(extracted_text) > 300 else extracted_text
            }
            
        except Exception as e:
            print(f"Error processing question: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Question answering error: {str(e)}")
            
        finally:
            cleanup_file(file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Question answering endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-questions-from-summary")
async def generate_questions_from_summary(
    summary: str,
    num_questions: int = 10,
    user = Depends(get_current_user)
):
    """Generate practice questions from summary text"""
    try:
        user_id = user["user"]["id"]
        print(f"Generating questions from summary for user: {user_id}")

        if not summary or len(summary.strip()) == 0:
            raise HTTPException(status_code=400, detail="Summary text is required")

        # Generate questions directly from summary
        questions = chatgpt_service.generate_questions(summary, num_questions)

        # Parse questions into structured format
        parsed_questions = parse_questions_response(questions)

        return {
            "success": True,
            "questions": parsed_questions,
            "total_questions": len(parsed_questions.get("questions", []))
        }

    except Exception as e:
        print(f"Summary question generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def parse_summary_response(summary_text: str) -> dict:
    """Parse the summary response into structured format"""
    try:
        lines = summary_text.split('\n')
        sections = {
            "english_summary": "",
            "urdu_summary": "",
            "key_points": [],
            "full_summary": summary_text
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if "ENGLISH SUMMARY:" in line:
                current_section = "english"
                sections["english_summary"] = line.replace("ENGLISH SUMMARY:", "").strip()
            elif "URDU SUMMARY:" in line:
                current_section = "urdu"
                sections["urdu_summary"] = line.replace("URDU SUMMARY:", "").strip()
            elif "KEY POINTS:" in line:
                current_section = "key_points"
            elif current_section == "english" and not line.startswith("URDU SUMMARY:") and not line.startswith("KEY POINTS:"):
                sections["english_summary"] += " " + line
            elif current_section == "urdu" and not line.startswith("KEY POINTS:"):
                sections["urdu_summary"] += " " + line
            elif current_section == "key_points" and (line.startswith("-") or line.startswith("•")):
                point = line.lstrip("-• ").strip()
                if point:
                    sections["key_points"].append(point)
        
        # Clean up summaries
        sections["english_summary"] = sections["english_summary"].strip()
        sections["urdu_summary"] = sections["urdu_summary"].strip()
        
        # If no key points found, extract some from the summary
        if not sections["key_points"] and sections["english_summary"]:
            # Simple extraction of key points by splitting sentences
            import re
            sentences = re.split(r'[.!?]+', sections["english_summary"])
            sections["key_points"] = [s.strip() for s in sentences if len(s.strip()) > 20][:5]
        
        return sections
        
    except Exception as e:
        print(f"Error parsing summary: {str(e)}")
        # Fallback if parsing fails
        return {
            "english_summary": summary_text,
            "urdu_summary": "",
            "key_points": ["Key point extraction failed"],
            "full_summary": summary_text
        }

def parse_questions_response(questions_text: str) -> dict:
    """Parse the questions response into structured format"""
    try:
        lines = questions_text.split('\n')
        sections = {
            "questions": [],
            "answers": [],
            "full_text": questions_text
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if "QUESTIONS:" in line:
                current_section = "questions"
            elif "ANSWERS:" in line:
                current_section = "answers"
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
        
        # Ensure we have matching questions and answers
        min_length = min(len(sections["questions"]), len(sections["answers"]))
        sections["questions"] = sections["questions"][:min_length]
        sections["answers"] = sections["answers"][:min_length]
        
        return sections
        
    except Exception as e:
        print(f"Error parsing questions: {str(e)}")
        # Fallback if parsing fails
        return {
            "questions": ["Question parsing failed"],
            "answers": ["Answer parsing failed"],
            "full_text": questions_text
        }

def parse_answer_response(answer_text: str) -> dict:
    """Parse the answer response into structured format"""
    try:
        lines = answer_text.split('\n')
        sections = {
            "answer": "",
            "source_reference": "",
            "confidence_level": "Medium",
            "full_response": answer_text
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if "ANSWER:" in line:
                current_section = "answer"
                sections["answer"] = line.replace("ANSWER:", "").strip()
            elif "SOURCE REFERENCE:" in line or "SOURCE REFERENCE (if available):" in line:
                current_section = "source"
                sections["source_reference"] = line.replace("SOURCE REFERENCE:", "").replace("SOURCE REFERENCE (if available):", "").strip()
            elif "CONFIDENCE LEVEL:" in line:
                current_section = "confidence"
                sections["confidence_level"] = line.replace("CONFIDENCE LEVEL:", "").strip()
            elif current_section == "answer" and not line.startswith("SOURCE REFERENCE:") and not line.startswith("CONFIDENCE LEVEL:"):
                sections["answer"] += " " + line
            elif current_section == "source" and not line.startswith("CONFIDENCE LEVEL:"):
                sections["source_reference"] += " " + line
            elif current_section == "confidence":
                sections["confidence_level"] = line
        
        # Clean up sections
        sections["answer"] = sections["answer"].strip()
        sections["source_reference"] = sections["source_reference"].strip()
        
        # If confidence level not found, try to detect from text
        if sections["confidence_level"] == "Medium":
            answer_lower = sections["answer"].lower()
            if "not covered" in answer_lower or "not found" in answer_lower or "not in the document" in answer_lower:
                sections["confidence_level"] = "Low"
            elif "clearly" in answer_lower or "specifically" in answer_lower or "according to" in answer_lower:
                sections["confidence_level"] = "High"
        
        return sections
        
    except Exception as e:
        print(f"Error parsing answer: {str(e)}")
        # Fallback if parsing fails
        return {
            "answer": answer_text,
            "source_reference": "",
            "confidence_level": "Medium",
            "full_response": answer_text
        }