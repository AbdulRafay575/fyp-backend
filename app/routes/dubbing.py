from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.services.dubbing_service import DubbingService
from app.services.auth_service import AuthService
import os
import uuid
import asyncio

router = APIRouter()
dubbing_service = DubbingService()
auth_service = AuthService()

# Store dubbing status in memory
dubbing_status = {}

# ✅ Request model to accept JSON body
class DubbingRequest(BaseModel):
    video_url: str
    target_language: str = "Urdu"

@router.post("/create")
async def create_dubbed_video(
    request: DubbingRequest,
    authorization: str = Header(None),
    background_tasks: BackgroundTasks = None
):
    """Create dubbed audio for YouTube video with background processing"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.replace("Bearer ", "")
        user = auth_service.get_current_user(token)
        user_id = user["user"]["id"]
        
        video_url = request.video_url
        target_language = request.target_language

        print(f"🎬 Creating dubbed video for user: {user_id}, video: {video_url}")

        # Generate unique job ID
        job_id = str(uuid.uuid4())
        dubbing_status[job_id] = {
            "status": "processing",
            "progress": 0,
            "video_url": video_url,
            "user_id": user_id,
            "error": None,
            "audio_file": None
        }

        # Start background processing
        if background_tasks:
            background_tasks.add_task(
                process_dubbing_job,
                job_id,
                video_url,
                target_language
            )
        else:
            # Immediate processing (for testing)
            asyncio.create_task(process_dubbing_job(job_id, video_url, target_language))

        return {
            "success": True,
            "job_id": job_id,
            "status": "processing",
            "message": "Dubbing process started"
        }

    except Exception as e:
        print(f"❌ Dubbing creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}")
async def get_dubbing_status(job_id: str, authorization: str = Header(None)):
    """Get status of dubbing job"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.replace("Bearer ", "")
        user = auth_service.get_current_user(token)

        status = dubbing_status.get(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")

        # Check if user owns this job
        if status.get("user_id") != user["user"]["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        return {
            "success": True,
            "job_id": job_id,
            **status
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"⚠️ Status check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_dubbed_audio(filename: str, authorization: str = Header(None)):
    """Download dubbed audio file"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")

        token = authorization.replace("Bearer ", "")
        auth_service.get_current_user(token)  # Verify token

        file_path = f"app/temp_uploads/{filename}"

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='audio/mpeg'
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"⚠️ Download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_dubbing_job(job_id: str, video_url: str, target_language: str):
    """Background task to process dubbing"""
    try:
        dubbing_status[job_id]["progress"] = 10
        dubbing_status[job_id]["status"] = "extracting_transcript"

        print(f"🧾 Extracting transcript for job {job_id}...")

        # Create synchronized audio
        print(f"🎧 Creating synchronized audio for job {job_id}...")
        dubbing_status[job_id]["progress"] = 50
        dubbing_status[job_id]["status"] = "creating_audio"

        audio_file_path = await dubbing_service.create_synchronized_audio(video_url, target_language)

        dubbing_status[job_id].update({
            "status": "completed",
            "progress": 100,
            "audio_file": audio_file_path,
            "download_url": f"/dubbing/download/{os.path.basename(audio_file_path)}"
        })

        print(f"✅ Dubbing completed for job {job_id}: {audio_file_path}")

    except Exception as e:
        print(f"❌ Dubbing processing error for job {job_id}: {str(e)}")
        dubbing_status[job_id].update({
            "status": "error",
            "error": str(e)
        })
