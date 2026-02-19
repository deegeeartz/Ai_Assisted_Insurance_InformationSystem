import google.generativeai as genai
import os

key = os.getenv("GOOGLE_API_KEY")
if not key:
    print("No API Key found")
    exit(1)

genai.configure(api_key=key, transport="rest")
print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Model: {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
