import os
from pathlib import Path
from typing import Dict, Optional
from instagrapi import Client

# session directory
SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)

class ClientManager:
    def __init__(self):
        self.clients: Dict[str, Client] = {}
    
    def get_session_file(self, username: str) -> Path:
        return SESSIONS_DIR / f"session_{username}.json"

    def get_client(self, username: str) -> Client:
        if username in self.clients:
            return self.clients[username]
        
        session_file = self.get_session_file(username)
        if not session_file.exists():
            raise ValueError(f"No session found for account '{username}'. Please log in first.")

        cl = Client()
        cl.load_settings(session_file)

        self.clients[username] = cl
        return cl

    def login_account(
        self,
        username: str,
        password: Optional[str] = None,
        session_id: Optional[str] = None,
        verification_code: Optional[str] = None
    ) -> Client:
        session_file = self.get_session_file(username)
        cl = Client()

        if session_file.exists():
            cl.load_settings(session_file, override_app_version=True)

        cl.set_country("US")
        cl.set_locale("en_US")

        if session_id:
            # Direct sessionid cookie login - 100% bypasses CAA and checkpoints
            try:
                cl.login_by_sessionid(session_id)
            except Exception:
                if session_file.exists():
                    # Retry with a clean client in case old settings contained an expired session
                    cl = Client()
                    cl.set_country("US")
                    cl.set_locale("en_US")
                    cl.login_by_sessionid(session_id)
                else:
                    raise
        elif password:
            cl.login(username, password, verification_code=verification_code)
        else:
            raise ValueError("Either password or session_id must be provided.")

        cl.dump_settings(session_file)

        self.clients[username] = cl
        return cl


client_manager = ClientManager()
