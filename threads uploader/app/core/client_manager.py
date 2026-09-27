from pathlib import Path
from typing import Dict, Optional
import os
import app.core.threads_patch
from threads_api.src.threads_api import ThreadsAPI
from app.config import SESSIONS_DIR


class ClientManager:
    def __init__(self):
        self.clients: Dict[str, ThreadsAPI] = {}
        os.makedirs(SESSIONS_DIR, exist_ok=True)

    def get_token_path(self, username: str) -> Path:
        return SESSIONS_DIR / f"token_{username}.dat"

    async def get_client(self, username: str) -> ThreadsAPI:
        if username in self.clients:
            client = self.clients[username]
            if getattr(client, "is_logged_in", False):
                return client

        token_path = self.get_token_path(username)
        api = ThreadsAPI()
        try:
            api.username = username
            token = None

            # Attempt 1: Check if token can be pulled from existing Instagram session
            try:
                from threads_api.src.http_sessions.instagrapi_session import InstagrapiSession
                s = InstagrapiSession()
                token = s.auth(username=username)
            except Exception:
                token = None

            # Attempt 2: If no token from IG session, check token_path
            if not token and token_path.exists():
                try:
                    import json
                    with open(token_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        res = api.load_settings(str(token_path))
                        import asyncio
                        if asyncio.iscoroutine(res):
                            await res
                        token = getattr(api, "token", None)
                except Exception:
                    pass

            if token:
                api.token = token
                api.auth_headers = {
                    'Authorization': f'Bearer IGT:2:{token}',
                    'User-Agent': 'Barcelona 289.0.0.77.109 Android',
                    'Sec-Fetch-Site': 'same-origin',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                }
                api.is_logged_in = True
                api.username = username
                self.clients[username] = api
                return api

            await api.close_gracefully()
            raise FileNotFoundError(
                f"No saved session found for account '{username}'. "
                f"Please log in first using POST /accounts/login."
            )
        except Exception as e:
            try:
                await api.close_gracefully()
            except Exception:
                pass
            raise RuntimeError(f"Failed to restore session for '{username}': {e}")

    async def login_account(
        self,
        username: str,
        password: str
    ) -> ThreadsAPI:
        token_path = self.get_token_path(username)
        api = ThreadsAPI()
        api.username = username
        try:
            login_result = await api.login(
                username=username,
                password=password,
                cached_token_path=str(token_path)
            )
            if login_result:
                res = api.dump_settings(str(token_path))
                import asyncio
                if asyncio.iscoroutine(res):
                    await res

                api.username = username
                api.is_logged_in = True
                self.clients[username] = api
                return api
            raise RuntimeError("Failed to authenticate with Threads. Verify credentials or challenge.")
        except Exception:
            try:
                await api.close_gracefully()
            except Exception:
                pass
            raise


    async def logout_account(self, username: str) -> bool:
        if username in self.clients:
            client = self.clients[username]
            try:
                await client.close_gracefully()
            except Exception:
                pass
            del self.clients[username]

        token_path = self.get_token_path(username)
        if token_path.exists():
            try:
                token_path.unlink()
            except Exception:
                pass
        return True


client_manager = ClientManager()