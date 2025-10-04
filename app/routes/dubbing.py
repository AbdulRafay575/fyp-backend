from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer
from app.services.dubbing_service import DubbingService
from app.services.auth_service import AuthService
import os

router = APIRouter()
dubbing_service = DubbingService()
auth_service = AuthService()
security = HTTPBearer()

@router.post("/create")
async def create_dubbed_video(video_url: str, target_language: str = "Urdu", token: str = Depends(security)):
    """Create dubbed audio for YouTube video"""
    try:
        user = auth_service.get_current_user(token)
        
        # Create synchronized audio
        audio_file_path = dubbing_service.create_synchronized_audio(video_url, target_language)
        
        return {
            "success": True,
            "video_url": video_url,
            "target_language": target_language,
            "audio_file": audio_file_path,
            "download_url": f"/dubbing/download/{os.path.basename(audio_file_path)}"
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{filename}")
async def download_dubbed_audio(filename: str):
    """Download dubbed audio file"""
    file_path = f"app/temp_uploads/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='audio/mpeg'
    )

