import google.generativeai as genai
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

# Setup Gemini
# In a real app, API Key should be in settings/env
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)

# We use the LangChain wrapper for easier integration with chains/parsers
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro-latest",
    temperature=0.1, # Low temp for deterministic logic extraction
    google_api_key=GOOGLE_API_KEY,
    convert_system_message_to_human=True 
)

def get_llm():
    return llm
