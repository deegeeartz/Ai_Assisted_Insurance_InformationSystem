import urllib.request
import urllib.error
import json

url = "http://localhost:8000/api/v1/underwrite"
payload = {
    "age": 35,
    "product_type": "life",
    "role": "consumer",
    "holder_name": "Test User",
    "coverage_selection": []
}

req = urllib.request.Request(
    url, method="POST",
    data=json.dumps(payload).encode("utf-8")
)
req.add_header("Content-Type", "application/json")

try:
    resp = urllib.request.urlopen(req)
    print(f"SUCCESS ({resp.code}):")
    print(json.dumps(json.loads(resp.read().decode()), indent=2))
except urllib.error.HTTPError as e:
    print(f"ERROR ({e.code}):")
    body = e.read().decode()
    print(body)
