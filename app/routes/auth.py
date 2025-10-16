from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()

# Pydantic models for request validation
class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/signup")
async def signup(request: SignupRequest):
    """User registration"""
    try:
        result = auth_service.signup(request.email, request.password, request.full_name)
        return {
            "success": True, 
            "user": result["user"],
            "message": "Account created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(request: LoginRequest):
    """User login"""
    try:
        result = auth_service.login(request.email, request.password)
        return {
            "success": True, 
            "user": result["user"],
            "access_token": result["session"]["access_token"],
            "message": "Logged in successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout")
async def logout():
    """User logout"""
    try:
        result = auth_service.logout()
        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@router.post("/forgot-password")
async def forgot_password(request: dict):
    email = request.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    return auth_service.reset_password(email)

@router.get("/verify-reset-token")
async def verify_reset_token(token: str):
    return auth_service.verify_reset_token(token)

@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    return auth_service.reset_password_with_token(req.token, req.new_password)



@router.get("/me")
async def get_current_user(authorization: str = Header(None)):
    """Get current user info"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.replace("Bearer ", "")
        result = auth_service.get_current_user(token)
        return {"success": True, "user": result["user"]}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))