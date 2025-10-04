from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
import time
from app.services.youtube_service import YouTubeService
from app.services.chatgpt_service import ChatGPTService
from app.services.auth_service import AuthService
from app.services.summary_service import SummaryService

router = APIRouter()
youtube_service = YouTubeService()
chatgpt_service = ChatGPTService()
auth_service = AuthService()
summary_service = SummaryService()

class YouTubeSummaryRequest(BaseModel):
    video_url: str
    chunk_minutes: Optional[int] = 5  # Reduced to 5 minutes for better handling
    target_language: Optional[str] = "Urdu"

@router.post("/summarize")
async def summarize_youtube_video(request: YouTubeSummaryRequest, authorization: str = Header(None)):
    """Get summary of YouTube video with improved long video handling"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.replace("Bearer ", "")
        user_data = auth_service.get_current_user(token)
        start_time = time.time()
        
        print(f"Processing YouTube video: {request.video_url}")
        
        # Get transcript with timestamps
        transcript = youtube_service.get_transcript_with_timestamps(request.video_url)
        if not transcript:
            raise HTTPException(status_code=400, detail="No transcript available for this video")
        
        print(f"Found {len(transcript)} transcript segments")
        
        # Get clean text only
        clean_text = youtube_service.get_transcript_text_only(transcript)
        
        print(f"Clean text length: {len(clean_text)} characters")
        
        # For long videos, use size-based chunking instead of time-based
        chunks = []
        if len(clean_text) > 8000:
            # Use size-based chunking for API limits
            chunks = youtube_service.chunk_transcript_by_size(clean_text, 6000)
            print(f"Using size-based chunking: {len(chunks)} chunks")
        elif len(clean_text) > 3000:
            # Use time-based chunking for medium videos
            chunks = youtube_service.chunk_transcript_by_time(transcript, request.chunk_minutes)
            print(f"Using time-based chunking: {len(chunks)} chunks")
        else:
            chunks = [clean_text]
            print("Using single chunk processing")
        
        # Generate summary
        if len(chunks) > 1:
            print("Using chunked summary approach...")
            summary = chatgpt_service.get_chunked_summary(chunks, request.target_language)
        else:
            print("Using single summary approach...")
            summary = chatgpt_service.get_summary(clean_text, request.target_language)
        
        processing_time = time.time() - start_time
        
        # Save to database
        saved_summary = None
        try:
            saved_summary = summary_service.save_summary(
                user_id=user_data["user"]["id"],
                title=f"YouTube Summary",
                content=summary,
                source_text=clean_text[:1000],  # Store first 1000 chars
                source_type="youtube"
            )
        except Exception as e:
            print(f"Failed to save summary: {e}")
        
        return {
            "success": True,
            "video_url": request.video_url,
            "transcript_segments": len(transcript),
            "chunks_processed": len(chunks),
            "summary": summary,
            "full_transcript": clean_text[:800] + "..." if len(clean_text) > 800 else clean_text,
            "processing_time": round(processing_time, 2),
            "saved_summary_id": saved_summary["id"] if saved_summary else None,
            "message": f"Processed {len(transcript)} segments in {len(chunks)} chunk(s)"
        }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"YouTube summarization error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process video: {str(e)}")