
import urllib.request
import json
import urllib.error
import urllib.parse
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(name, url, method="GET", data=None):
    print(f"--- Testing {name} ({method} {url}) ---")
    try:
        req = urllib.request.Request(url, method=method)
        req.add_header('Content-Type', 'application/json')
        
        if data:
            json_data = json.dumps(data).encode('utf-8')
            req.data = json_data

        with urllib.request.urlopen(req) as response:
            status = response.code
            body = response.read().decode('utf-8')
            print(f"Status: {status}")
            try:
                parsed = json.loads(body)
                print(f"Response: {json.dumps(parsed, indent=2)}")
            except:
                print(f"Response: {body}")
            return True
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        print(e.read().decode('utf-8'))
        return False
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        print("Is the server running?")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    print("\n")

def main():
    # 1. Health/Root check
    test_endpoint("Root Health", "http://localhost:8000/health")

    # 2. Chat Endpoint (GET? No, it's POST based on main.py/underwrite.py)
    # The endpoint is @router.post("/chat") in underwrite.py
    # Args are (message: str, role: str) -> Query params by default in FastAPI
    params = urllib.parse.urlencode({
        "message": "I want to buy life insurance for my family",
        "role": "consumer"
    })
    chat_url = f"{BASE_URL}/underwrite/chat?{params}"
    test_endpoint("AI Chat", chat_url, method="POST")

    # 3. Underwrite Endpoint
    # @router.post("/underwrite")
    # Body: UnderwriteRequest
    # coverage_selection needs to match schema: List[CoverageBlock]
    # CoverageBlock = {id, name, description, base_price, icon, enabled}
    # This is complex to mock manually if it validates strict schema.
    # Let's try sending minimal valid payload.
    # coverage_selection default is [].
    
    underwrite_payload = {
        "age": 35,
        "natural_language_query": "I need full coverage for life",
        "role": "consumer",
        "holder_name": "Test User",
        "holder_email": "test@example.com",
        "coverage_selection": [] 
    }
    
    test_endpoint("AI Underwrite", f"{BASE_URL}/underwrite/underwrite", method="POST", data=underwrite_payload)

if __name__ == "__main__":
    main()
