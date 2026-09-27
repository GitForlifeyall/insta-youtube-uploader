"""
Compatibility patch for threads-api with Pydantic v2.

threads-api 1.2.0 uses fields with leading underscores (_typename),
which was valid in Pydantic v1 but raises NameError in Pydantic v2.
This patch pre-compiles `threads_api.src.types` with `pydantic.v1`
so ThreadsAPI works seamlessly alongside modern FastAPI and Pydantic v2.
"""

import sys
import types
import os
import importlib.util
import pydantic.v1 as pydantic_v1

def apply_threads_patch():
    if "threads_api.src.types" in sys.modules:
        return

    # Try locating threads_api
    spec = importlib.util.find_spec("threads_api")
    if not spec or not spec.origin:
        return

    threads_api_dir = os.path.dirname(spec.origin)
    types_path = os.path.join(threads_api_dir, "src", "types.py")

    if not os.path.exists(types_path):
        return

    types_mod = types.ModuleType("threads_api.src.types")
    types_mod.__dict__["pydantic"] = pydantic_v1
    types_mod.__dict__["BaseModel"] = pydantic_v1.BaseModel
    types_mod.__dict__["Field"] = pydantic_v1.Field

    with open(types_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Direct types to use pydantic.v1
    code = code.replace("from pydantic import", "from pydantic.v1 import")
    exec(code, types_mod.__dict__)
    sys.modules["threads_api.src.types"] = types_mod

    # Patch InstagrapiSession to reuse existing Instagram sessions without password challenges
    try:
        from threads_api.src.http_sessions.instagrapi_session import InstagrapiSession
        orig_auth = InstagrapiSession.auth

        def patched_auth(self, **kwargs):
            username = kwargs.get("username")
            if username:
                from pathlib import Path
                ig_session = Path(__file__).resolve().parent.parent.parent.parent / "Insta+Facebook uploader" / "sessions" / f"session_{username}.json"
                if ig_session.exists():
                    try:
                        self._instagrapi_client.load_settings(ig_session)
                        auth_header = self._instagrapi_client.private.headers.get("Authorization", "")
                        if "Bearer IGT:2:" in auth_header:
                            token = auth_header.split("Bearer IGT:2:")[1]
                            self._instagrapi_client.private.headers = self._threads_headers
                            return token
                    except Exception:
                        pass
            return orig_auth(self, **kwargs)

        InstagrapiSession.auth = patched_auth
    except Exception:
        pass

    # Patch AioHTTPSession to safely close sessions and suppress unclosed session warnings
    try:
        import warnings
        warnings.filterwarnings("ignore", category=ResourceWarning, message=".*Unclosed client session.*")

        import aiohttp.client
        aiohttp.client.ClientSession.__del__ = lambda self, *args, **kwargs: None

        from threads_api.src.http_sessions.aiohttp_session import AioHTTPSession
        
        async def safe_close(self):
            if hasattr(self, "_session") and self._session and not self._session.closed:
                try:
                    await self._session.close()
                except Exception:
                    pass
            self._session = None
            self._instagrapi_client = None

        AioHTTPSession.close = safe_close
    except Exception:
        pass

# Apply immediately on import
apply_threads_patch()

