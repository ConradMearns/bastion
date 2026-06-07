"""JWT authentication utilities."""

import os
from datetime import datetime, timedelta, timezone

import jwt

SECRET = os.environ.get("BASTION_JWT_SECRET", "6b86bc96188ed8afe2bfae2be02f367954d3036bd2fef576ced75a95af63a23a")
ALGORITHM = "HS256"
TOKEN_EXPIRY_DAYS = 365


def create_token(hostname: str) -> str:
    """Create a JWT token for a host."""
    payload = {
        "sub": hostname,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRY_DAYS),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify a JWT token and return its payload."""
    return jwt.decode(token, SECRET, algorithms=[ALGORITHM])
