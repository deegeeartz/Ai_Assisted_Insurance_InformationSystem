"""Debug: inspect what response.content actually looks like."""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "debug_response.txt")

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

async def main():
    with open(LOG, "w", encoding="utf-8") as f:
        f.write("=== LLM Response Inspection ===\n\n")

    from app.core.config import settings
    from app.core.llm import get_llm
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_llm()

    # Simple test message
    log("--- Test 1: Simple chat ---")
    response = llm.invoke([HumanMessage(content="Say hello in one sentence.")])
    log(f"Type of content: {type(response.content)}")
    log(f"Content repr: {repr(response.content)}")
    log(f"Content str: {str(response.content)}")

    # JSON-requesting message (like underwriting)
    log("\n--- Test 2: JSON request (like underwriting) ---")
    response2 = llm.invoke([
        SystemMessage(content="You are a JSON API. Respond ONLY with valid JSON. No markdown."),
        HumanMessage(content='Return this JSON: {"status": "approved", "reason": "test"}')
    ])
    log(f"Type of content: {type(response2.content)}")
    log(f"Content repr: {repr(response2.content)}")
    
    if isinstance(response2.content, list):
        log(f"List length: {len(response2.content)}")
        for i, part in enumerate(response2.content):
            log(f"  Part {i}: type={type(part).__name__}, repr={repr(part)}")
            if hasattr(part, 'text'):
                log(f"    .text = {repr(part.text)}")
            if isinstance(part, dict):
                log(f"    keys = {list(part.keys())}")
                if 'text' in part:
                    log(f"    ['text'] = {repr(part['text'])}")

    log("\n=== Done ===")
    print(f"Log written to: {LOG}")

asyncio.run(main())
