import requests
import json
import time

BASE_URL = "http://localhost:8000"
USERNAME = "my_threads_username"
PASSWORD = "my_threads_password"


def test_api():
    print("=" * 60)
    print("1. Testing Server Health Check...")
    print("=" * 60)
    try:
        res = requests.get(f"{BASE_URL}/")
        print("Status Code:", res.status_code)
        print("Response:", json.dumps(res.json(), indent=2))
    except Exception as e:
        print(f"Failed to connect to server at {BASE_URL}. Is uvicorn running?")
        print("Run: uvicorn app.main:app --reload --port 8000")
        print("Error:", e)
        return

    print("\n" + "=" * 60)
    print(f"2. Logging in as '{USERNAME}'...")
    print("=" * 60)
    login_payload = {
        "username": USERNAME,
        "password": PASSWORD
    }

    try:
        login_res = requests.post(f"{BASE_URL}/accounts/login", json=login_payload)
        print("Status Code:", login_res.status_code)
        print("Response:", json.dumps(login_res.json(), indent=2))

        if login_res.status_code != 200:
            print("\n[!] Login failed or credentials placeholder used.")
            print("To test real posting, update USERNAME and PASSWORD at the top of test_api.py.")
            return
    except Exception as e:
        print("Error during login request:", e)
        return

    print("\n" + "=" * 60)
    print("3. Checking Account Status...")
    print("=" * 60)
    status_res = requests.get(f"{BASE_URL}/accounts/{USERNAME}/status")
    print("Status Code:", status_res.status_code)
    print("Response:", json.dumps(status_res.json(), indent=2))

    print("\n" + "=" * 60)
    print(f"4. Fetching Threads Profile for '{USERNAME}'...")
    print("=" * 60)
    profile_res = requests.get(f"{BASE_URL}/accounts/{USERNAME}/profile")
    print("Status Code:", profile_res.status_code)
    print("Response:", json.dumps(profile_res.json(), indent=2))

    print("\n" + "=" * 60)
    print("5. Publishing a Text Thread...")
    print("=" * 60)
    text_payload = {
        "username": USERNAME,
        "text": f"Hello Threads from Threads Automation API! 🚀 (Timestamp: {int(time.time())})",
        "url": "https://github.com"
    }
    text_res = requests.post(f"{BASE_URL}/posts/text", json=text_payload)
    print("Status Code:", text_res.status_code)
    print("Response:", json.dumps(text_res.json(), indent=2))

    created_post = text_res.json()
    post_id = created_post.get("media_id")

    if post_id:
        print("\n" + "=" * 60)
        print(f"6. Liking the newly created post [{post_id}]...")
        print("=" * 60)
        like_payload = {
            "username": USERNAME,
            "post_id": post_id
        }
        like_res = requests.post(f"{BASE_URL}/posts/like", json=like_payload)
        print("Status Code:", like_res.status_code)
        print("Response:", json.dumps(like_res.json(), indent=2))

    print("\n" + "=" * 60)
    print("All Automated Tests Completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_api()
