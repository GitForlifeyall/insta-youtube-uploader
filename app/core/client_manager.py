import os
from pathlib import Path
from typing import Dict, Optional
from instagrapi import Client

from app.config import SESSIONS_DIR
from app.core import database

class ClientManager:
    def __init__(self):
        self.clients: Dict[str, Client] = {}

    def get_proxy(self, username: str) -> Optional[str]:
        return database.get_account_proxy(username)

    def set_proxy(self, username: str, proxy: Optional[str]) -> Optional[str]:
        cleaned_proxy = database.set_account_proxy(username, proxy)

        # Apply to live client if cached
        if username in self.clients:
            cl = self.clients[username]
            cl.set_proxy(cleaned_proxy)
        return cleaned_proxy

    def get_session_file(self, username: str) -> Path:
        return SESSIONS_DIR / f"session_{username}.json"

    def get_client(self, username: str) -> Client:
        proxy = self.get_proxy(username)
        if username in self.clients:
            cl = self.clients[username]
            if getattr(cl, "proxy", None) != proxy:
                cl.set_proxy(proxy)
            return cl
        
        session_file = self.get_session_file(username)
        if not session_file.exists():
            raise ValueError(f"No session found for account '{username}'. Please log in first.")

        cl = Client()
        if proxy:
            cl.set_proxy(proxy)

        cl.load_settings(session_file)
        if proxy:
            cl.set_proxy(proxy)

        self.clients[username] = cl
        return cl

    def login_account(
        self,
        username: str,
        password: Optional[str] = None,
        session_id: Optional[str] = None,
        verification_code: Optional[str] = None,
        totp_secret: Optional[str] = None,
        proxy: Optional[str] = None
    ) -> Client:
        from app.core import totp

        if proxy is not None:
            self.set_proxy(username, proxy)

        configured_proxy = self.get_proxy(username)
        session_file = self.get_session_file(username)
        cl = Client()

        if configured_proxy:
            cl.set_proxy(configured_proxy)

        if session_file.exists():
            cl.load_settings(session_file, override_app_version=True)
            if configured_proxy:
                cl.set_proxy(configured_proxy)

        cl.set_country("US")
        cl.set_locale("en_US")

        # Resolve dynamic 6-digit TOTP code if secret or key is provided
        active_totp_secret = totp_secret
        resolved_2fa_code = verification_code

        # If user passed a secret key in the verification_code field (e.g. 16+ chars base32)
        if resolved_2fa_code and totp.is_totp_secret(resolved_2fa_code):
            active_totp_secret = resolved_2fa_code
            resolved_2fa_code = totp.generate_totp_code(active_totp_secret)
        elif active_totp_secret:
            resolved_2fa_code = totp.generate_totp_code(active_totp_secret)

        if session_id:
            # Direct sessionid cookie login - 100% bypasses CAA and checkpoints
            try:
                cl.login_by_sessionid(session_id)
            except Exception:
                if session_file.exists():
                    # Retry with a clean client in case old settings contained an expired session
                    cl = Client()
                    if configured_proxy:
                        cl.set_proxy(configured_proxy)
                    cl.set_country("US")
                    cl.set_locale("en_US")
                    cl.login_by_sessionid(session_id)
                else:
                    raise
        elif password:
            cl.login(username, password, verification_code=resolved_2fa_code or "")
        else:
            raise ValueError("Either password or session_id must be provided.")

        cl.dump_settings(session_file)

        # Persist profile credentials & proxy in SQLite database
        try:
            database.save_account_profile(
                username=username,
                password=password,
                session_id=session_id,
                totp_secret=active_totp_secret,
                proxy=configured_proxy,
                user_id=str(getattr(cl, "user_id", "")) if getattr(cl, "user_id", None) else None
            )
        except Exception as db_err:
            print(f"Warning: could not record account in database: {db_err}")

        self.clients[username] = cl
        return cl

    def list_saved_accounts(self):
        usernames = set()
        for file in SESSIONS_DIR.glob("session_*.json"):
            u = file.stem.replace("session_", "").strip()
            if u:
                usernames.add(u)
        for row in database.get_all_db_accounts():
            if row.get("username"):
                usernames.add(row["username"])
        return sorted(list(usernames))

    def get_active_accounts(self):
        return [{"username": u} for u in self.list_saved_accounts()]

    def delete_session(self, username: str) -> bool:
        session_file = self.get_session_file(username)
        if username in self.clients:
            del self.clients[username]

        # Clean up account from database
        database.delete_account_from_db(username)

        if session_file.exists():
            session_file.unlink()
            return True
        return False


client_manager = ClientManager()
