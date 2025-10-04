from app.database.supabase_client import supabase
from datetime import datetime
from typing import Optional, Dict, Any

class SummaryService:
    def save_summary(self, user_id: str, title: str, content: str, source_text: str, source_type: str) -> Optional[Dict[str, Any]]:
        """Save summary to database"""
        try:
            result = supabase.table("summaries").insert({
                "title": title,
                "content": content,
                "source_text": source_text,
                "source_type": source_type,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception:
            # If table doesn't exist or other error, return None
            return None
    
    def update_summary(self, summary_id: int, content: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Update summary content"""
        try:
            result = supabase.table("summaries").update({
                "content": content,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", summary_id).eq("user_id", user_id).execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception:
            return None