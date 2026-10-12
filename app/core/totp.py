"""
TOTP (2FA) Generator and Account String Parser.
Generates dynamic 6-digit two-factor authentication codes from secret keys (RFC 6238)
using standard Python libraries (no external dependencies required).
"""
import base64
import hashlib
import hmac
import struct
import time
from typing import Optional, Tuple


def generate_totp_code(secret: str) -> str:
    """
    Generates a 6-digit TOTP code (RFC 6238) from a base32 secret key.
    Automatically handles spaces and missing padding.
    """
    if not secret:
        raise ValueError("Secret key cannot be empty.")
        
    key = secret.replace(" ", "").strip().upper()
    padding = len(key) % 8
    if padding != 0:
        key += "=" * (8 - padding)
        
    try:
        key_bytes = base64.b32decode(key)
    except Exception as e:
        raise ValueError(f"Invalid Base32 TOTP secret: {e}")
    
    interval = 30
    counter = int(time.time() // interval)
    counter_bytes = struct.pack(">Q", counter)
    
    h = hmac.new(key_bytes, counter_bytes, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = (struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF) % 1000000
    return f"{code:06d}"


def is_totp_secret(text: str) -> bool:
    """Checks if text looks like a base32 TOTP secret key rather than a 6-digit numeric verification code."""
    if not text:
        return False
    clean = text.replace(" ", "").strip().upper()
    # TOTP secrets are typically 16, 26, or 32 characters base32
    if len(clean) >= 12 and not clean.isdigit():
        return True
    return False


def parse_purchased_account_string(raw: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parses purchased account strings in common market formats:
    - Tab-separated: username \\t password \\t 2fa_secret
    - Colon-separated: username:password:2fa_secret
    - Pipe-separated: username|password|2fa_secret
    - Space-separated
    Returns (username, password, totp_secret)
    """
    raw = raw.strip()
    if not raw:
        return None, None, None

    parts = []
    if "\t" in raw:
        parts = [p.strip() for p in raw.split("\t") if p.strip()]
    elif "|" in raw:
        parts = [p.strip() for p in raw.split("|") if p.strip()]
    elif ":" in raw and not (raw.startswith("http://") or raw.startswith("https://") or raw.startswith("socks5://")):
        parts = [p.strip() for p in raw.split(":") if p.strip()]
    else:
        # Fallback split
        tokens = raw.split()
        if len(tokens) >= 2:
            parts = [tokens[0], tokens[1], " ".join(tokens[2:])]
        else:
            parts = tokens

    username = parts[0] if len(parts) > 0 else None
    password = parts[1] if len(parts) > 1 else None
    totp_secret = parts[2] if len(parts) > 2 else None

    return username, password, totp_secret
