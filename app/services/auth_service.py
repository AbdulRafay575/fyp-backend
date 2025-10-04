from app.database.supabase_client import supabase
from supabase import Client
from fastapi import HTTPException
import os

class AuthService:
    def __init__(self):
        self.client: Client = supabase
    
    def signup(self, email: str, password: str, full_name: str):
        """User registration"""
        try:
            # Create auth user
            auth_response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name
                    },
                    "email_redirect_to": "http://localhost:3000/login"  # ✅ moved outside

                }
            })
            
            if auth_response.user:
                return {
                    "user": {
                        "id": auth_response.user.id,
                        "email": auth_response.user.email,
                        "user_metadata": auth_response.user.user_metadata or {}
                    }
                }
            
            raise Exception("Failed to create user")
            
        except Exception as e:
            raise Exception(f"Signup error: {str(e)}")
    
    def login(self, email: str, password: str):
        """User login"""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            # Check if session exists
            if not response.session:
                raise Exception("Login failed: No session returned")
                
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "user_metadata": response.user.user_metadata or {}
                },
                "session": {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token
                }
            }
        except Exception as e:
            raise Exception(f"Login error: {str(e)}")
    
    def logout(self):
        """User logout"""
        try:
            response = self.client.auth.sign_out()
            return {"message": "Logged out successfully"}
        except Exception as e:
            raise Exception(f"Logout error: {str(e)}")
    
    def get_current_user(self, token: str):
        """Get current user from token"""
        try:
            response = self.client.auth.get_user(token)
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "user_metadata": response.user.user_metadata or {}
                }
            }
        except Exception as e:
            raise Exception(f"Authentication error: {str(e)}")
    
    def reset_password(self, email: str):
        """Password reset request - Updated for Supabase flow"""
        try:
            # This will send an email with a reset link that redirects to your frontend
            response = self.client.auth.reset_password_for_email(
                email,
                {
                    "redirectTo": "http://localhost:3000/reset-password"
                }
            )
            return {"message": "Password reset email sent"}
        except Exception as e:
            raise Exception(f"Password reset error: {str(e)}")
    
    def update_password(self, new_password: str):
        """Update password for authenticated user"""
        try:
            response = self.client.auth.update_user({
                "password": new_password
            })
            return {"message": "Password updated successfully"}
        except Exception as e:
            raise Exception(f"Password update error: {str(e)}")
    
    def verify_reset_token(self, token: str):
        """Verify if the reset token is valid"""
        try:
            # Use the token to get user info
            response = self.client.auth.get_user(token)
            return {
                "valid": True,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email
                }
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def reset_password_with_token(self, token: str, new_password: str):
        """Reset password using the token from email"""
        try:
            # First verify the token
            verification = self.verify_reset_token(token)
            if not verification["valid"]:
                raise Exception("Invalid or expired reset token")
            
            # Update the password
            response = self.client.auth.update_user({
                "password": new_password
            })
            
            return {"message": "Password reset successfully"}
        except Exception as e:
            raise Exception(f"Password reset error: {str(e)}")