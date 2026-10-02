import hmac

from fastapi import Header, HTTPException, status

from app.config import get_settings

settings = get_settings()


def verify_admin_token(x_admin_token: str = Header(None)) -> bool:
    """Verifies admin authorization token using constant-time comparison."""
    if not x_admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication token required in 'x-admin-token' header.",
        )

    expected = settings.ADMIN_SECRET_KEY.encode("utf-8")
    provided = x_admin_token.encode("utf-8")

    if not hmac.compare_digest(expected, provided):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid administrative authorization token.",
        )

    return True
