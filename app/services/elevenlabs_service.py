from elevenlabs import generate, set_api_key
from app.config import settings
import aiohttp
import json

class ElevenLabsService:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        set_api_key(self.api_key)
        self.default_voice_id = "kvQSb3naDTi3sgHwwBC1"

    # -------------------
    # Synchronous TTS
    # -------------------
    def text_to_speech(self, text: str, voice_id: str = None) -> bytes:
        """
        Convert text to speech synchronously using ElevenLabs
        Returns audio bytes
        """
        try:
            voice_id = voice_id or self.default_voice_id
            audio_bytes = generate(
                text=text,
                voice=voice_id,
                model="eleven_multilingual_v2"
            )
            return audio_bytes
        except Exception as e:
            raise Exception(f"ElevenLabs TTS error: {str(e)}")

    # -------------------
    # Asynchronous TTS
    # -------------------
    async def text_to_speech_async(self, text: str, voice_id: str = None) -> bytes:
        """
        Convert text to speech asynchronously via ElevenLabs API
        """
        try:
            voice_id = voice_id or self.default_voice_id
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }

            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=30) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        error_text = await response.text()
                        raise Exception(f"ElevenLabs API error: {error_text}")
        except Exception as e:
            raise Exception(f"ElevenLabs async TTS error: {str(e)}")

    # -------------------
    # Save audio to file
    # -------------------
    def save_audio_to_file(self, audio_bytes: bytes, file_path: str):
        """Save audio bytes to file"""
        try:
            with open(file_path, "wb") as f:
                f.write(audio_bytes)
        except Exception as e:
            raise Exception(f"Audio save error: {str(e)}")
