import os
import logging

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

_llm = None

def get_llm():
    global _llm
    if _llm is not None:
        return _llm

    if not GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not set. AI features will be unavailable.")
        raise RuntimeError("GOOGLE_API_KEY not configured. Set it in .env to enable AI features.")

    try:
        import google.generativeai as genai
        from langchain_google_genai import ChatGoogleGenerativeAI

        genai.configure(api_key=GOOGLE_API_KEY)
        _llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro-latest",
            temperature=0.1,
            google_api_key=GOOGLE_API_KEY,
            convert_system_message_to_human=True
        )
        return _llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        raise

