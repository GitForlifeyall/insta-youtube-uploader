"""
🌐 Instagram Isolated Session Handler & Cookie Harvester
=========================================================
Launches an isolated Chromium browser profile (Brave/Edge) per account.
Because each brand has its own dedicated profile folder:
  - You log in manually once
  - Account switching NEVER invalidates or overwrites sessions
  - Cookies (sessionid, ds_user_id) are automatically extracted via CDP
  - Automatically updates root .env, session files, and syncs Social Hub
"""

import os
import sys
import time
import json
import socket
import logging
import argparse
import subprocess
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SessionHarvester")

PROJECTS_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECTS_ROOT / ".env"
PROFILES_DIR = PROJECTS_ROOT / "data" / "browser_profiles"
INSTA_FB_API_URL = os.getenv("INSTA_FB_API_URL", "http://localhost:8001")
SOCIAL_HUB_API_URL = os.getenv("SOCIAL_HUB_API_URL", "http://localhost:8000")

# Candidate browser paths on Windows
BROWSER_CANDIDATES = [
    Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
]


def find_browser() -> Path:
    for p in BROWSER_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError("No Chromium browser (Brave, Edge, Chrome) found in default paths.")


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def get_brand_ig_usernames() -> Dict[str, int]:
    """Scans .env and returns a map of {ig_username: brand_index}."""
    result = {}
    if not ENV_PATH.exists():
        return result
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        for i in range(1, 10):
            prefix = f"BRAND{i}_IG_USERNAME="
            if line.startswith(prefix):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    result[val.lower()] = i
    return result


def update_env_session_id(username: str, session_id: str) -> bool:
    """Updates the matching BRAND<N>_IG_SESSION_ID in root .env."""
    if not ENV_PATH.exists():
        logger.warning(f".env not found at {ENV_PATH}")
        return False

    brand_map = get_brand_ig_usernames()
    target_idx = brand_map.get(username.lower())

    with open(ENV_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    updated = False
    new_lines = []

    target_key = f"BRAND{target_idx}_IG_SESSION_ID" if target_idx else None

    for line in lines:
        stripped = line.strip()
        if target_key and stripped.startswith(f"{target_key}="):
            new_lines.append(f"{target_key}={session_id}")
            updated = True
        elif not target_key and stripped.startswith("BRAND1_IG_SESSION_ID="):
            new_lines.append(f"BRAND1_IG_SESSION_ID={session_id}")
            updated = True
        else:
            new_lines.append(line)

    if not updated and target_key:
        new_lines.append(f"{target_key}={session_id}")
        updated = True

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")

    logger.info(f"💾 Updated {target_key or 'BRAND1_IG_SESSION_ID'} in .env")
    return True


PORTABLE_SESSIONS_DIR = PROJECTS_ROOT / "data" / "browser_sessions"
PORTABLE_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def get_portable_cookie_file(username: str) -> Path:
    return PORTABLE_SESSIONS_DIR / f"cookies_{username.lower()}.json"


def get_env_session_id(username: str) -> Optional[str]:
    brand_map = get_brand_ig_usernames()
    idx = brand_map.get(username.lower())
    if not idx or not ENV_PATH.exists():
        return None
    key = f"BRAND{idx}_IG_SESSION_ID"
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith(f"{key}="):
                val = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return val
    return None


def load_portable_cookies(username: str) -> list:
    fpath = get_portable_cookie_file(username)
    if fpath.exists():
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) >= 2:
                    return data
        except Exception as e:
            logger.warning(f"Could not read portable cookies file {fpath}: {e}")
    return []


def save_portable_cookies(username: str, cookies: list) -> bool:
    fpath = get_portable_cookie_file(username)
    try:
        valid_keys = {"name", "value", "domain", "path", "secure", "httpOnly", "sameSite", "expires"}
        cookie_params = [{k: c[k] for k in valid_keys if k in c} for c in cookies]
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(cookie_params, f, indent=2)
        logger.info(f"💾 Saved {len(cookie_params)} portable cookies to {fpath.name}")
        return True
    except Exception as e:
        logger.warning(f"Failed to save portable cookies to {fpath}: {e}")
        return False


def get_page_target(port: int) -> Optional[Tuple[str, str]]:
    """Returns (webSocketDebuggerUrl, current_url) for the active Instagram tab."""
    try:
        r = requests.get(f"http://127.0.0.1:{port}/json", timeout=1)
        if r.status_code == 200:
            targets = r.json()
            # Prioritize instagram tab
            for t in targets:
                if t.get("type") == "page" and "instagram.com" in t.get("url", ""):
                    ws_url = t.get("webSocketDebuggerUrl")
                    if ws_url:
                        return ws_url, t.get("url", "")
            # Fallback to any open page
            for t in targets:
                if t.get("type") == "page":
                    ws_url = t.get("webSocketDebuggerUrl")
                    if ws_url:
                        return ws_url, t.get("url", "")
    except Exception:
        pass
    return None


async def harvest_cookies_via_cdp(port: int, target_username: str, max_wait_seconds: int = 180) -> Optional[Dict[str, str]]:
    """
    Connects to Chromium DevTools Protocol on 127.0.0.1:{port} using page-level targets,
    auto-clears invalid cookies on ?e= error, and captures fresh authenticated cookies.
    """
    import websockets

    start_time = time.time()
    logger.info(f"⏳ Waiting for browser tab on port {port}...")

    page_target = None
    while time.time() - start_time < 20:
        page_target = get_page_target(port)
        if page_target:
            break
        await asyncio.sleep(0.5)

    if not page_target:
        raise RuntimeError("Could not find active browser tab.")

    logger.info(f"👉 Opened browser for @{target_username}. Please log in in the opened browser window...")

    cleared_on_error = False
    poll_start = time.time()

    while time.time() - poll_start < max_wait_seconds:
        page_target = get_page_target(port)
        if not page_target:
            await asyncio.sleep(1)
            continue

        ws_url, current_url = page_target

        try:
            async with websockets.connect(ws_url, max_size=10_000_000, close_timeout=2) as ws:
                msg_id = 1
                await ws.send(json.dumps({"id": msg_id, "method": "Network.enable"}))
                await ws.recv()

                # If Instagram redirected with ?e= parameter, cookies are invalid
                if ("?e=" in current_url or "error" in current_url) and not cleared_on_error:
                    logger.warning(f"⚠️ Stale/expired session detected ({current_url})")
                    logger.info("🧹 Clearing browser cookies so you get a clean login form...")
                    msg_id += 1
                    await ws.send(json.dumps({"id": msg_id, "method": "Network.clearBrowserCookies"}))
                    await ws.recv()

                    # Wipe stale cookie file
                    cookie_file = get_portable_cookie_file(target_username)
                    if cookie_file.exists():
                        try:
                            cookie_file.unlink()
                        except Exception:
                            pass

                    msg_id += 1
                    await ws.send(json.dumps({
                        "id": msg_id,
                        "method": "Page.navigate",
                        "params": {"url": "https://www.instagram.com/accounts/login/"}
                    }))
                    await ws.recv()
                    cleared_on_error = True
                    logger.info(f"👉 Clean login form ready! Enter credentials for @{target_username}...")
                    await asyncio.sleep(2)
                    continue

                # Query current cookies
                msg_id += 1
                await ws.send(json.dumps({
                    "id": msg_id,
                    "method": "Network.getCookies",
                    "params": {"urls": ["https://www.instagram.com", "https://instagram.com"]}
                }))
                res_raw = await ws.recv()
                res = json.loads(res_raw)

                cookies = res.get("result", {}).get("cookies", [])
                cookie_dict = {c["name"]: c["value"] for c in cookies if "name" in c and "value" in c}

                # Valid login requires both sessionid AND ds_user_id, and URL not on login/error page
                is_on_login_or_error = "accounts/login" in current_url or "?e=" in current_url
                if "sessionid" in cookie_dict and "ds_user_id" in cookie_dict and not is_on_login_or_error:
                    session_id = cookie_dict["sessionid"]
                    ds_user_id = cookie_dict["ds_user_id"]

                    if len(session_id) > 20:
                        logger.info("🎉 Instagram authenticated session verified!")
                        save_portable_cookies(target_username, cookies)

                        return {
                            "session_id": session_id,
                            "ds_user_id": ds_user_id,
                            "csrftoken": cookie_dict.get("csrftoken", ""),
                            "mid": cookie_dict.get("mid", "")
                        }

        except (websockets.exceptions.ConnectionClosed, Exception) as e:
            # Reconnect on next loop iteration
            pass

        await asyncio.sleep(1.5)

    return None





def run_harvester(username: str, timeout: int = 180, close_on_success: bool = True) -> Dict[str, Any]:
    browser_exe = find_browser()
    profile_dir = PROFILES_DIR / username
    profile_dir.mkdir(parents=True, exist_ok=True)
    port = get_free_port()

    logger.info(f"🚀 Launching {browser_exe.name} with dedicated profile: {profile_dir.name}")
    cmd = [
        str(browser_exe),
        f"--user-data-dir={profile_dir}",
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-sync",
        "https://www.instagram.com/"
    ]

    proc = subprocess.Popen(cmd)

    try:
        cookies = asyncio.run(harvest_cookies_via_cdp(port, username, max_wait_seconds=timeout))
        if not cookies or not cookies.get("session_id"):
            return {"status": "error", "message": "Timed out waiting for login cookies."}

        session_id = cookies["session_id"]
        update_env_session_id(username, session_id)

        # Sync to Insta+Facebook uploader service
        try:
            res = requests.post(
                f"{INSTA_FB_API_URL}/accounts/login",
                json={"username": username, "session_id": session_id},
                timeout=15
            )
            if res.status_code == 200:
                logger.info(f"✅ Uploader service authenticated for @{username}!")
            else:
                logger.warning(f"⚠️ Uploader returned status {res.status_code}: {res.text[:100]}")
        except Exception as e:
            logger.warning(f"Could not reach uploader on {INSTA_FB_API_URL}: {e}")

        # Sync Social Hub
        try:
            requests.post(f"{SOCIAL_HUB_API_URL}/api/sync-credentials", timeout=10)
            logger.info("✅ Social Hub workspace synchronized!")
        except Exception:
            pass

        return {
            "status": "success",
            "username": username,
            "session_id": session_id[:20] + "...",
            "profile_dir": str(profile_dir)
        }

    finally:
        if close_on_success:
            try:
                proc.terminate()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description="Instagram Isolated Session Harvester")
    parser.add_argument("username", nargs="?", help="Instagram username (e.g. lyr.ical786)")
    parser.add_argument("--timeout", type=int, default=180, help="Login timeout in seconds")
    parser.add_argument("--keep-open", action="store_true", help="Keep browser open after harvesting")
    args = parser.parse_args()

    brand_map = get_brand_ig_usernames()
    username = args.username

    if not username:
        if brand_map:
            print("\nConfigured Instagram accounts found in .env:")
            usernames = list(brand_map.keys())
            for idx, u in enumerate(usernames, 1):
                print(f"  [{idx}] @{u}")
            choice = input(f"\nSelect account [1-{len(usernames)}] or enter username: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(usernames):
                username = usernames[int(choice) - 1]
            else:
                username = choice.lstrip("@")
        else:
            username = input("Enter Instagram username to harvest: ").strip().lstrip("@")

    if not username:
        print("Error: No username provided.")
        sys.exit(1)

    print(f"\n=======================================================")
    print(f"🔑 Harvesting session for Instagram account: @{username}")
    print(f"=======================================================\n")

    res = run_harvester(username, timeout=args.timeout, close_on_success=not args.keep_open)
    if res["status"] == "success":
        print("\n" + "=" * 55)
        print(f"🎉 SUCCESS! Session captured for @{username}")
        print(f"   Saved to isolated profile: {res['profile_dir']}")
        print(f"   Updated root .env and live backend sessions.")
        print("=" * 55 + "\n")
    else:
        print(f"\n❌ Error: {res.get('message')}\n")


if __name__ == "__main__":
    main()
