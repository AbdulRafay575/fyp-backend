import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY")
    
settings = Settings()