# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.config import settings

# # Import routers
# from app.routes.auth import router as auth_router
# from app.routes.users import router as users_router
# from app.routes.documents import router as documents_router
# from app.routes.summaries import router as summaries_router
# from app.routes.past_papers import router as past_papers_router
# from app.routes.questions import router as questions_router
# from app.routes.youtube import router as youtube_router
# from app.routes.dubbing import router as dubbing_router

# app = FastAPI(
#     title="FYP Backend API",
#     description="AI-Powered Document Processing System for Final Year Project",
#     version="1.0.0",
#     docs_url="/docs",
#     redoc_url="/redoc"
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React frontend
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include routers
# app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
# app.include_router(users_router, prefix="/users", tags=["Users"])
# app.include_router(documents_router, prefix="/documents", tags=["Documents"])
# app.include_router(summaries_router, prefix="/summaries", tags=["Summaries"])
# app.include_router(past_papers_router, prefix="/past-papers", tags=["Past Papers"])
# app.include_router(questions_router, prefix="/questions", tags=["Questions"])
# app.include_router(youtube_router, prefix="/youtube", tags=["YouTube"])
# app.include_router(dubbing_router, prefix="/dubbing", tags=["Dubbing"])

# @app.get("/")
# async def root():
#     """Root endpoint with API information"""
#     return {
#         "message": "FYP Backend API is running!",
#         "version": "1.0.0",
#         "docs": "/docs",
#         "endpoints": {
#             "authentication": "/auth",
#             "users": "/users",
#             "documents": "/documents",
#             "summaries": "/summaries",
#             "past_papers": "/past-papers", 
#             "questions": "/questions",
#             "youtube": "/youtube",
#             "dubbing": "/dubbing"
#         }
#     }

# @app.get("/health")
# async def health_check():
#     """Health check endpoint"""
#     return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

# @app.get("/api-info")
# async def api_info():
#     """API information endpoint"""
#     return {
#         "name": "FYP Backend API",
#         "version": "1.0.0",
#         "description": "AI-Powered Document Processing System",
#         "author": "Your Name",
#         "features": [
#             "User Authentication",
#             "Document Processing & OCR",
#             "AI Summarization", 
#             "Question Generation",
#             "Past Paper Analysis",
#             "YouTube Video Summarization",
#             "YouTube Dubbing"
#         ]
#     }


from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings

# Import routers
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.documents import router as documents_router
from app.routes.summaries import router as summaries_router
from app.routes.past_papers import router as past_papers_router
from app.routes.questions import router as questions_router
from app.routes.youtube import router as youtube_router
from app.routes.dubbing import router as dubbing_router

app = FastAPI(
    title="FYP Backend API (Temporary - No Auth)",
    description="AI-Powered Document Processing System for FYP (Temporary)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers as normal
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(documents_router, prefix="/documents", tags=["Documents"])
app.include_router(summaries_router, prefix="/summaries", tags=["Summaries"])
app.include_router(past_papers_router, prefix="/past-papers", tags=["Past Papers"])
app.include_router(questions_router, prefix="/questions", tags=["Questions"])
app.include_router(youtube_router, prefix="/youtube", tags=["YouTube"])
app.include_router(dubbing_router, prefix="/dubbing", tags=["Dubbing"])

# --- Temporary override to ignore auth ---
@app.middleware("http")
async def bypass_auth_middleware(request: Request, call_next):
    """
    Temporarily bypass authentication for all routes.
    Useful for testing without signing in.
    """
    try:
        # You could inject a dummy user into request.state if needed
        request.state.user = {
            "id": "temporary-user",
            "email": "test@example.com",
            "role": "authenticated"
        }
        response = await call_next(request)
        return response
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

# Root endpoints
@app.get("/")
async def root():
    return {
        "message": "FYP Backend API (Temporary - No Auth) is running!",
        "version": "1.0.0",
        "docs": "/docs",
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api-info")
async def api_info():
    return {
        "name": "FYP Backend API",
        "version": "1.0.0",
        "description": "AI-Powered Document Processing System",
        "features": [
            "User Authentication (temporarily bypassed)",
            "Document Processing & OCR",
            "AI Summarization",
            "Question Generation",
            "Past Paper Analysis",
            "YouTube Video Summarization",
            "YouTube Dubbing"
        ]
    }
