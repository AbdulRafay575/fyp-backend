from fastapi import APIRouter, HTTPException, Depends, Header, UploadFile, File
from pydantic import BaseModel
from app.services.auth_service import AuthService
from app.database.supabase_client import supabase  # Add this import
import base64
import os

router = APIRouter()
auth_service = AuthService()

# Pydantic models for request validation
class UpdateProfileRequest(BaseModel):
    full_name: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.get("/profile")
async def get_profile(authorization: str = Header(None)):
    """Get user profile"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.replace("Bearer ", "")
        user_data = auth_service.get_current_user(token)
        
        # Get user profile from Supabase profiles table
        profile_result = supabase.table("profiles").select("*").eq("id", user_data["user"]["id"]).execute()
        
        user_profile = user_data["user"]
        if profile_result.data:
            # Merge with profile data
            profile_data = profile_result.data[0]
            user_profile.update({
                "full_name": profile_data.get("full_name", user_data["user"].get("user_metadata", {}).get("full_name", "")),
                "profile_picture": profile_data.get("profile_picture")
            })
        
        return {
            "success": True, 
            "user": user_profile
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.put("/profile")
async def update_profile(request: UpdateProfileRequest, authorization: str = Header(None)):
    """Update user profile"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.replace("Bearer ", "")
        user_data = auth_service.get_current_user(token)
        
        # Update user profile in Supabase profiles table
        update_data = {
            "full_name": request.full_name,
            "updated_at": "now()"
        }
        
        # Check if profile exists, if not create it
        profile_result = supabase.table("profiles").select("*").eq("id", user_data["user"]["id"]).execute()
        
        if profile_result.data:
            # Update existing profile
            result = supabase.table("profiles").update(update_data).eq("id", user_data["user"]["id"]).execute()
        else:
            # Create new profile
            update_data["id"] = user_data["user"]["id"]
            update_data["email"] = user_data["user"]["email"]
            update_data["created_at"] = "now()"
            result = supabase.table("profiles").insert(update_data).execute()
        
        if result.data:
            updated_user = {
                "id": user_data["user"]["id"],
                "email": user_data["user"]["email"],
                "full_name": request.full_name,
                "user_metadata": {
                    "full_name": request.full_name,
                    **user_data["user"].get("user_metadata", {})
                }
            }
            
            return {
                "success": True, 
                "user": updated_user,
                "message": "Profile updated successfully"
            }
        else:
            raise Exception("Failed to update profile")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/profile-picture")
async def update_profile_picture(file: UploadFile = File(...), authorization: str = Header(None)):
    """Update user profile picture"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.replace("Bearer ", "")
        user_data = auth_service.get_current_user(token)
        
        # Read and encode the image
        contents = await file.read()
        image_b64 = base64.b64encode(contents).decode('utf-8')
        
        # Update profile picture in Supabase
        update_data = {
            "profile_picture": f"data:{file.content_type};base64,{image_b64}",
            "updated_at": "now()"
        }
        
        # Check if profile exists, if not create it
        profile_result = supabase.table("profiles").select("*").eq("id", user_data["user"]["id"]).execute()
        
        if profile_result.data:
            result = supabase.table("profiles").update(update_data).eq("id", user_data["user"]["id"]).execute()
        else:
            update_data["id"] = user_data["user"]["id"]
            update_data["email"] = user_data["user"]["email"]
            update_data["full_name"] = user_data["user"].get("user_metadata", {}).get("full_name", "")
            update_data["created_at"] = "now()"
            result = supabase.table("profiles").insert(update_data).execute()
        
        if result.data:
            return {
                "success": True, 
                "message": "Profile picture updated successfully",
                "profile_picture": update_data["profile_picture"]
            }
        else:
            raise Exception("Failed to update profile picture")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/change-password")
async def change_password(request: ChangePasswordRequest, authorization: str = Header(None)):
    """Change user password"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.replace("Bearer ", "")
        user_data = auth_service.get_current_user(token)
        
        # Update password using auth service
        result = auth_service.update_password(request.new_password)
        
        return {
            "success": True, 
            "message": "Password updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))