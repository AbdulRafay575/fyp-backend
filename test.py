import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

model = genai.GenerativeModel("gemini-3-pro-preview")

response = model.generate_content(
    "Explain how AI works in a few words"
)

print(response.text)
