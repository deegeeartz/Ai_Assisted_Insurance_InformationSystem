import requests
import os
import time

BASE_URL = "http://localhost:8000/api/v1"
MANUALS_DIR = "/app/app/manuals"

def get_token():
    email = os.environ.get("SEED_ADMIN_EMAIL")
    password = os.environ.get("SEED_ADMIN_PASSWORD")
    if not email or not password:
        print("Set SEED_ADMIN_EMAIL and SEED_ADMIN_PASSWORD in the environment to seed manuals.")
        return None
    max_retries = 5
    for i in range(max_retries):
        try:
            print(f"Attempting login... (Try {i+1}/{max_retries})")
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={"email": email, "password": password},
            )
            if response.status_code == 200:
                print("Login successful!")
                return response.json()["access_token"]
            else:
                print(f"Login failed (Status {response.status_code}): {response.text}")
        except Exception as e:
            print(f"Connection error: {e}")
        time.sleep(2)
    return None

def upload_manual(token, filename, product_type):
    file_path = os.path.join(MANUALS_DIR, filename)
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"Uploading {filename}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Reload file pointer for each request ensures clean state
    with open(file_path, "rb") as f:
        files = {"file": (filename, f, "text/plain")}
        data = {"product_type": product_type, "version": "v1"}

        try:
            response = requests.post(f"{BASE_URL}/manuals/upload", headers=headers, files=files, data=data)
            if response.status_code == 200:
                print(f"Successfully uploaded {filename}")
                print(f"Response: {response.json()}")
            else:
                print(f"Failed to upload {filename}: {response.text}")
        except Exception as e:
            print(f"Error uploading {filename}: {e}")

if __name__ == "__main__":
    print("Starting Manual Seeding...")
    token = get_token()
    if token:
        upload_manual(token, "heirs_general_auto.txt", "auto")
        upload_manual(token, "heirs_life_term.txt", "life")
        upload_manual(token, "heirs_gadget_device.txt", "gadget")
    else:
        print("Could not obtain token. Aborting.")
