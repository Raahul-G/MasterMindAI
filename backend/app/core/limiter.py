from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.security import decode_access_token


def _get_user_key(request: Request) -> str:
    """Rate limit key: user ID from JWT if valid, otherwise client IP."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        user_id = decode_access_token(auth[7:])
        if user_id:
            return user_id
    return get_remote_address(request)


limiter = Limiter(key_func=_get_user_key)
