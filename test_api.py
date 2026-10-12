import requests
import json
import time

BASE_URL = "http://localhost:8000"
USERNAME = "lulop.123"
PASSWORD = "Beliver123@"
SESSION_ID = "59840897323%3Acyvs9pXSASa0UG%3A29%3AAYn4-R4W0YitxOtwcDU1tRwuEU3JG0kuMYQ_1x2gfg"

def test_api():
    print("=" * 50)
    print("1. Testing Server Health Check...")
    print("=" * 50)
    try:
        res = requests.get(f"{BASE_URL}/")
        print("Status Code:", res.status_code)
        print("Response:", json.dumps(res.json(), indent=2))
    except Exception as e:
        print(f"Failed to connect to server at {BASE_URL}. Is uvicorn running?")
        print("Error:", e)
        return

    print("\n" + "=" * 50)
    print(f"2. Logging in as '{USERNAME}'...")
    print("=" * 50)
    login_payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "session_id": SESSION_ID,
        "verification_code": None
    }
    
    try:
        login_res = requests.post(f"{BASE_URL}/accounts/login", json=login_payload)
        print("Status Code:", login_res.status_code)
        print("Response:", json.dumps(login_res.json(), indent=2))
        
        if login_res.status_code != 200:
            print("\n[!] Login did not succeed. Check credentials or Instagram challenge.")
            return
    except Exception as e:
        print("Error during login request:", e)
        return

    print("\n" + "=" * 50)
    print("3. Checking Account Status...")
    print("=" * 50)
    status_res = requests.get(f"{BASE_URL}/accounts/{USERNAME}/status")
    print("Status Code:", status_res.status_code)
    print("Response:", json.dumps(status_res.json(), indent=2))

    print("\n" + "=" * 50)
    print("4. Searching Instagram Official Music Catalogue...")
    print("=" * 50)
    search_params = {
        "username": USERNAME,
        "query": "Starboy"
    }
    music_res = requests.get(f"{BASE_URL}/music/search", params=search_params)
    print("Status Code:", music_res.status_code)
    tracks_data = music_res.json()
    
    tracks = tracks_data.get("tracks", [])
    print(f"Found {len(tracks)} tracks matching 'Starboy':")
    starboy_track = None
    for i, t in enumerate(tracks[:3], 1):
        print(f"  {i}. {t['title']} - {t['display_artist']} (Cluster ID: {t['audio_cluster_id']})")
        if "the weeknd" in t['display_artist'].lower() and starboy_track is None:
            starboy_track = t

    target_cluster_id = starboy_track["audio_cluster_id"] if starboy_track else "2373614659537666"

    print("\n" + "=" * 50)
    print("5. Uploading Reel with 'Starboy' Audio in Background...")
    print("=" * 50)
    reel_payload = {
        "username": USERNAME,
        "video_path": "12598818_1080_1920_60fps.mp4",
        "caption": "Reel with Starboy by The Weeknd playing in the background! 🚀🎵 #fyp #reels",
        "music_query": "Starboy The Weeknd"
    }
    
    print("Sending upload request to server (this can take 15-30s)...")
    start_time = time.time()
    upload_res = requests.post(f"{BASE_URL}/upload/reel", json=reel_payload)
    duration = round(time.time() - start_time, 2)
    
    print(f"Upload Status Code: {upload_res.status_code} (took {duration}s)")
    print("Response:", json.dumps(upload_res.json(), indent=2))

    print("\n" + "=" * 50)
    print("Tests Completed Successfully!")
    print("=" * 50)

if __name__ == "__main__":
    test_api()
