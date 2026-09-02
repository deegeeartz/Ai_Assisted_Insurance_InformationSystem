import logging

logger = logging.getLogger(__name__)

_llm = None

def get_llm():
    global _llm
    if _llm is not None:
        return _llm

    from app.core.config import settings

    api_key = settings.GOOGLE_API_KEY

    if not api_key:
        logger.warning("GOOGLE_API_KEY not set. AI features will be unavailable.")
        raise RuntimeError("GOOGLE_API_KEY not configured. Set it in .env to enable AI features.")

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        _llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            temperature=0.1,
            google_api_key=api_key,
        )
        logger.info("LLM initialized: gemini-3.6-flash")
        return _llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        raise
