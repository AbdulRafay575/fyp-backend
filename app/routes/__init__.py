# Routes package
from .auth import router as auth_router
from .users import router as users_router
from .documents import router as documents_router
from .summaries import router as summaries_router
from .past_papers import router as past_papers_router
from .questions import router as questions_router
from .youtube import router as youtube_router
from .dubbing import router as dubbing_router

__all__ = [
    "auth_router",
    "users_router", 
    "documents_router",
    "summaries_router",
    "past_papers_router",
    "questions_router",
    "youtube_router",
    "dubbing_router"
]