import google.generativeai as genai
import os
import requests

key = os.getenv("GOOGLE_API_KEY")
print(f"Testing key: {key[:5]}...{key[-5:]}")

# Test 1: REST API direct (bypass library)
print("\n--- Test 1: REST API (curl equivalent) ---")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
data = {
    "contents": [{
        "parts": [{"text": "Hello"}]
    }]
}
try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"REST failed: {e}")

# Test 2: Library
print("\n--- Test 2: Google GenAI Library ---")
try:
    genai.configure(api_key=key, transport="rest")
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello")
    print(f"Library Success! Response: {response.text}")
except Exception as e:
    print(f"Library Failed: {e}")
