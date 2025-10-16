from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.services.auth_service import AuthService
from app.database.supabase_client import supabase

router = APIRouter()
auth_service = AuthService()

# Pydantic models for request validation
class SummaryCreateRequest(BaseModel):
    title: str
    content: str
    source_text: Optional[str] = None
    source_type: str
    document_id: Optional[int] = None

class SummaryUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    source_text: Optional[str] = None

class SummaryResponse(BaseModel):
    id: int
    title: str
    content: str
    source_text: Optional[str] = None
    source_type: str
    user_id: str
    document_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

def handle_table_error(e):
    """Handle table not found errors gracefully"""
    error_msg = str(e)
    if "PGRST205" in error_msg or "table" in error_msg.lower() and "not found" in error_msg.lower():
        return {
            "success": True,
            "summaries": [],
            "count": 0,
            "message": "No summaries table found. Table will be created when you generate your first summary."
        }
    raise e

@router.get("/", response_model=dict)
async def get_user_summaries(authorization: str = Header(None)):
    """Get all summaries for current user"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.replace("Bearer ", "")
        user_data = auth_service.get_current_user(token)
        
        # Get summaries from Supabase
        result = supabase.table("summaries").select("*").eq("user_id", user_data["user"]["id"]).execute()
        
        if result.data:
            summaries = [
                SummaryResponse(
                    id=summary["id"],
                    title=summary["title"],
                    content=summary["content"],
                    source_text=summary.get("source_text"),
                    source_type=summary["source_type"],
                    user_id=summary["user_id"],
                    document_id=summary.get("document_id"),
                    created_at=summary["created_at"],
                    updated_at=summary["updated_at"]
                ) for summary in result.data
            ]
        else:
            summaries = []
        
        return {
            "success": True, 
            "summaries": summaries,
            "count": len(summaries)
        }
        
    except Exception as e:
        # Handle table not found error gracefully
        return handle_table_error(e)

@router.post("/", response_model=dict)
async def create_summary(request: SummaryCreateRequest, authorization: str = Header(None)):
    """Create a new summary"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.replace("Bearer ", "")
        user_data = auth_service.get_current_user(token)
        
        # Insert summary into Supabase
        result = supabase.table("summaries").insert({
            "title": request.title,
            "content": request.content,
            "source_text": request.source_text,
            "source_type": request.source_type,
            "user_id": user_data["user"]["id"],
            "document_id": request.document_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
        
        if result.data:
            summary_data = result.data[0]
            summary = SummaryResponse(
                id=summary_data["id"],
                title=summary_data["title"],
                content=summary_data["content"],
                source_text=summary_data.get("source_text"),
                source_type=summary_data["source_type"],
                user_id=summary_data["user_id"],
                document_id=summary_data.get("document_id"),
                created_at=summary_data["created_at"],
                updated_at=summary_data["updated_at"]
            )
            
            return {
                "success": True, 
                "summary": summary,
                "message": "Summary created successfully"
            }
        else:
            raise Exception("Failed to create summary")
            
    except Exception as e:
        # If table doesn't exist, provide helpful message
        error_msg = str(e)
        if "PGRST205" in error_msg or "table" in error_msg.lower() and "not found" in error_msg.lower():
            return {
                "success": False,
                "message": "Summaries table not found. Please create the table in your Supabase database first."
            }
        raise HTTPException(status_code=400, detail=str(e))

# For other routes, return empty responses until table exists
@router.get("/{summary_id}", response_model=dict)
async def get_summary(summary_id: int, authorization: str = Header(None)):
    """Get specific summary"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        return {
            "success": False,
            "message": "Summaries table not available yet."
        }
        
    except Exception as e:
        return handle_table_error(e)

@router.put("/{summary_id}", response_model=dict)
async def update_summary(summary_id: int, request: SummaryUpdateRequest, authorization: str = Header(None)):
    """Update summary content"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.replace("Bearer ", "")
        user_data = auth_service.get_current_user(token)
        
        # Build update data
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        if request.title is not None:
            update_data["title"] = request.title
        if request.content is not None:
            update_data["content"] = request.content
        if request.source_text is not None:
            update_data["source_text"] = request.source_text
        
        # Update summary in Supabase
        result = supabase.table("summaries").update(update_data).eq("id", summary_id).eq("user_id", user_data["user"]["id"]).execute()
        
        if result.data:
            summary_data = result.data[0]
            summary = SummaryResponse(
                id=summary_data["id"],
                title=summary_data["title"],
                content=summary_data["content"],
                source_text=summary_data.get("source_text"),
                source_type=summary_data["source_type"],
                user_id=summary_data["user_id"],
                document_id=summary_data.get("document_id"),
                created_at=summary_data["created_at"],
                updated_at=summary_data["updated_at"]
            )
            
            return {
                "success": True, 
                "summary": summary,
                "message": "Summary updated successfully"
            }
        else:
            return {
                "success": False,
                "message": "Summary not found or you don't have permission to update it"
            }
            
    except Exception as e:
        error_msg = str(e)
        if "PGRST205" in error_msg or "table" in error_msg.lower() and "not found" in error_msg.lower():
            return {
                "success": False,
                "message": "Summaries table not found. Please create the table in your Supabase database first."
            }
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{summary_id}", response_model=dict)
async def delete_summary(summary_id: int, authorization: str = Header(None)):
    """Delete a summary permanently"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")

        token = authorization.replace("Bearer ", "")
        user_data = auth_service.get_current_user(token)
        user_id = user_data["user"]["id"]

        # Try deleting summary for current user
        result = (
            supabase.table("summaries")
            .delete()
            .eq("id", summary_id)
            .eq("user_id", user_id)
            .execute()
        )

        if result.data:
            return {"success": True, "message": "Summary deleted successfully."}
        else:
            return {
                "success": False,
                "message": "Summary not found or you don't have permission to delete it.",
            }

    except Exception as e:
        return handle_table_error(e)

@router.delete("/delete/all", response_model=dict)
async def delete_all_summaries(authorization: str = Header(None)):
    """Delete all summaries of the current user"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")

        token = authorization.replace("Bearer ", "")
        user_data = auth_service.get_current_user(token)
        user_id = user_data["user"]["id"]

        supabase.table("summaries").delete().eq("user_id", user_id).execute()

        return {"success": True, "message": "All summaries deleted successfully."}

    except Exception as e:
        return handle_table_error(e)


@router.get("/search/", response_model=dict)
async def search_summaries(query: str, authorization: str = Header(None)):
    """Search summaries by title or content"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        return {
            "success": True,
            "summaries": [],
            "query": query,
            "count": 0,
            "message": "Summaries table not available yet."
        }
        
    except Exception as e:
        return handle_table_error(e)