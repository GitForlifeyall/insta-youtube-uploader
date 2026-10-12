"""
Browser Login Manager.
Launches a real Chromium browser (Brave, Chrome, or Edge) routed through the user's proxy,
navigates to Instagram, allows the user to log in naturally (handling 2FA or captchas),
and extracts the authenticated sessionid cookie and saves the session to disk and SQLite database.
"""
import os
import threading
import time
from urllib.parse import urlparse
from typing import Optional, Dict, Any
from instagrapi import Client

from app.core import database
from app.core.client_manager import client_manager


class BrowserLoginManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.active_session: Optional[Dict[str, Any]] = None
        self._browser_instance = None
        self._context_instance = None
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def get_browser_executable(self) -> Optional[str]:
        candidates = [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def parse_proxy(self, proxy_str: Optional[str]):
        if not proxy_str or not proxy_str.strip():
            return None, None
        formatted = database.format_proxy_string(proxy_str.strip())
        if not formatted:
            return None, None
        parsed = urlparse(formatted)
        proxy_config = {
            "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
        }
        if parsed.username:
            proxy_config["username"] = parsed.username
        if parsed.password:
            proxy_config["password"] = parsed.password
        return proxy_config, formatted

    def start_login(
        self,
        proxy: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        with self._lock:
            # Stop any previous session
            if self.active_session and self.active_session.get("status") in ["running", "waiting_for_user"]:
                self.stop_login()

            browser_path = self.get_browser_executable()
            if not browser_path:
                raise ValueError("No supported Chromium browser (Brave, Chrome, or Edge) found on system.")

            proxy_config, formatted_proxy = self.parse_proxy(proxy)

            self._stop_event.clear()
            self.active_session = {
                "status": "starting",
                "proxy": formatted_proxy,
                "proxy_config": proxy_config,
                "browser_path": browser_path,
                "hint_username": username,
                "hint_password": password,
                "username": None,
                "session_id": None,
                "error": None,
                "started_at": time.time()
            }

            self._thread = threading.Thread(target=self._browser_worker, daemon=True)
            self._thread.start()

            return {
                "success": True,
                "status": "starting",
                "proxy": formatted_proxy,
                "browser": os.path.basename(browser_path)
            }

    def _browser_worker(self):
        from playwright.sync_api import sync_playwright

        session = self.active_session
        proxy_config = session.get("proxy_config")
        browser_path = session.get("browser_path")
        formatted_proxy = session.get("proxy")

        try:
            with sync_playwright() as p:
                launch_args = {
                    "executable_path": browser_path,
                    "headless": False,
                    "args": [
                        "--disable-blink-features=AutomationControlled",
                        "--start-maximized"
                    ]
                }
                if proxy_config:
                    launch_args["proxy"] = proxy_config

                browser = p.chromium.launch(**launch_args)
                self._browser_instance = browser
                context = browser.new_context(
                    viewport=None,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
                self._context_instance = context
                page = context.new_page()

                session["status"] = "waiting_for_user"
                page.goto("https://www.instagram.com/accounts/login/", timeout=60000)

                # Monitor cookies until sessionid appears or stopped
                while not self._stop_event.is_set():
                    time.sleep(1.2)
                    try:
                        cookies = context.cookies("https://www.instagram.com")
                    except Exception:
                        # Window closed by user
                        break

                    session_cookie = next((c for c in cookies if c.get("name") == "sessionid"), None)
                    if session_cookie and session_cookie.get("value"):
                        sid = session_cookie["value"]
                        session["session_id"] = sid
                        session["status"] = "extracting"

                        try:
                            resolved_user = self._complete_session(sid, formatted_proxy, session.get("hint_password"))
                            session["username"] = resolved_user
                            session["status"] = "success"
                        except Exception as auth_err:
                            session["status"] = "error"
                            session["error"] = f"Failed to save authenticated session: {auth_err}"
                        break

                    # Check if browser was closed manually by user
                    if not browser.is_connected():
                        break

                time.sleep(1.0)
                try:
                    browser.close()
                except Exception:
                    pass

        except Exception as e:
            session["status"] = "error"
            session["error"] = str(e)
        finally:
            if session.get("status") == "waiting_for_user":
                session["status"] = "cancelled"
            self._browser_instance = None
            self._context_instance = None

    def _complete_session(self, session_id: str, proxy: Optional[str], password: Optional[str] = None) -> str:
        """Saves session into instagrapi client_manager and SQLite database."""
        cl = Client()
        if proxy:
            cl.set_proxy(proxy)
        cl.login_by_sessionid(session_id)
        info = cl.account_info()
        username = info.username

        # Save session file and database record
        client_manager.login_account(
            username=username,
            password=password,
            session_id=session_id,
            proxy=proxy
        )
        return username

    def force_extract(self) -> Dict[str, Any]:
        """Called when user explicitly clicks 'I Have Logged In'."""
        with self._lock:
            if not self.active_session:
                return {"success": False, "detail": "No active browser login session."}

            if self.active_session.get("status") == "success":
                return {
                    "success": True,
                    "status": "success",
                    "username": self.active_session.get("username")
                }

            if not self._context_instance:
                return {"success": False, "detail": "Browser is not active or was closed."}

            try:
                cookies = self._context_instance.cookies("https://www.instagram.com")
                session_cookie = next((c for c in cookies if c.get("name") == "sessionid"), None)
                if not session_cookie or not session_cookie.get("value"):
                    return {
                        "success": False,
                        "detail": "Session cookie not detected yet. Please ensure you are logged into your account in the browser window."
                    }

                sid = session_cookie["value"]
                self.active_session["session_id"] = sid
                self.active_session["status"] = "extracting"

                formatted_proxy = self.active_session.get("proxy")
                resolved_user = self._complete_session(sid, formatted_proxy, self.active_session.get("hint_password"))
                self.active_session["username"] = resolved_user
                self.active_session["status"] = "success"

                self.stop_login()

                return {
                    "success": True,
                    "status": "success",
                    "username": resolved_user
                }
            except Exception as e:
                return {"success": False, "detail": str(e)}

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            if not self.active_session:
                return {"status": "idle"}
            return {
                "status": self.active_session.get("status"),
                "username": self.active_session.get("username"),
                "proxy": self.active_session.get("proxy"),
                "error": self.active_session.get("error")
            }

    def stop_login(self):
        self._stop_event.set()
        if self._browser_instance:
            try:
                self._browser_instance.close()
            except Exception:
                pass

    def open_account_browser(self, username: str) -> Dict[str, Any]:
        """
        Opens a visible browser window (Brave, Chrome, or Edge) routed through
        the account's assigned proxy, with the account's session cookies injected,
        so the user is already logged in on Instagram!
        """
        import json
        from app.config import SESSIONS_DIR

        # 1. Fetch account proxy and session data
        proxy = database.get_account_proxy(username)
        session_file = SESSIONS_DIR / f"session_{username}.json"

        session_id = None
        user_id = None
        if session_file.exists():
            try:
                with open(session_file, "r") as f:
                    data = json.load(f)
                session_id = data.get("authorization_data", {}).get("sessionid") or data.get("cookies", {}).get("sessionid")
                user_id = data.get("authorization_data", {}).get("ds_user_id") or data.get("cookies", {}).get("ds_user_id")
            except Exception:
                pass

        if not session_id:
            acc = database.get_account(username)
            if acc:
                session_id = acc.get("session_id")
                user_id = acc.get("user_id")

        if not session_id:
            raise ValueError(f"No active session found for @{username}. Please log in first.")

        browser_path = self.get_browser_executable()
        if not browser_path:
            raise ValueError("No supported Chromium browser found on system.")

        proxy_config, formatted_proxy = self.parse_proxy(proxy)

        # Launch in background thread so the HTTP request completes immediately
        threading.Thread(
            target=self._run_account_browser,
            args=(username, session_id, user_id, browser_path, proxy_config),
            daemon=True
        ).start()

        return {
            "success": True,
            "message": f"Browser opened for @{username}",
            "username": username,
            "proxy": formatted_proxy,
            "browser": os.path.basename(browser_path)
        }

    def _run_account_browser(self, username: str, session_id: str, user_id: Optional[str], browser_path: str, proxy_config: Optional[dict]):
        from playwright.sync_api import sync_playwright
        try:
            with sync_playwright() as p:
                launch_args = {
                    "executable_path": browser_path,
                    "headless": False,
                    "args": [
                        "--disable-blink-features=AutomationControlled",
                        "--start-maximized"
                    ]
                }
                if proxy_config:
                    launch_args["proxy"] = proxy_config

                browser = p.chromium.launch(**launch_args)
                context = browser.new_context(
                    viewport=None,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )

                cookies = [
                    {
                        "name": "sessionid",
                        "value": session_id,
                        "domain": ".instagram.com",
                        "path": "/",
                        "httpOnly": True,
                        "secure": True,
                        "sameSite": "Lax"
                    }
                ]
                if user_id:
                    cookies.append({
                        "name": "ds_user_id",
                        "value": str(user_id),
                        "domain": ".instagram.com",
                        "path": "/",
                        "httpOnly": False,
                        "secure": True,
                        "sameSite": "Lax"
                    })

                context.add_cookies(cookies)
                page = context.new_page()
                page.goto(f"https://www.instagram.com/{username}/")

                # Keep browser open while window is connected
                while browser.is_connected():
                    time.sleep(1.0)
        except Exception as e:
            print(f"Browser window for @{username} closed or encountered error: {e}")


browser_login_manager = BrowserLoginManager()
