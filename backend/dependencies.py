from fastapi import Cookie, Header, HTTPException, status

try:
    from backend.config import settings
    from backend.services.auth_service import get_user_by_token
except ModuleNotFoundError:
    from config import settings
    from services.auth_service import get_user_by_token


def get_current_user(
    authorization: str | None = Header(default=None),
    session_cookie: str | None = Cookie(default=None, alias=settings.session_cookie_name),
):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()
    elif session_cookie:
        token = session_cookie

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    user = get_user_by_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )
    return user
