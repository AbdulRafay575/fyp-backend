import requests
import base64
import os
from app.config import settings

class OCRService:
    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.endpoint = "https://models.github.ai/inference"
        self.model = "openai/gpt-4.1"  # Vision-capable model
    
    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text from image using GPT-4 Vision API
        """
        try:
            # Read and encode image
            with open(image_path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode("utf-8")
            
            # Prepare request payload
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an OCR assistant. Extract all readable text from the image exactly as it appears. Preserve formatting, line breaks, and special characters."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract all text from this image exactly as it appears:"},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                        ]
                    }
                ],
                "temperature": 0
            }
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            # Send request
            response = requests.post(
                f"{self.endpoint}/chat/completions", 
                headers=headers, 
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            extracted_text = result["choices"][0]["message"]["content"]
            
            return extracted_text
            
        except Exception as e:
            raise Exception(f"OCR extraction error: {str(e)}")
    
    def extract_text_from_bytes(self, image_bytes: bytes) -> str:
        """
        Extract text from image bytes
        """
        try:
            # Save bytes to temporary file and process
            temp_path = "app/temp_uploads/temp_ocr_image.png"
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            with open(temp_path, "wb") as f:
                f.write(image_bytes)
            
            return self.extract_text_from_image(temp_path)
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)