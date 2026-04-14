import sqlite3

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
try:
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token
except ModuleNotFoundError:
    google_requests = None
    google_id_token = None

try:
    from backend.config import settings
    from backend.dependencies import get_current_user
    from backend.rate_limiter import enforce_rate_limit
    from backend.services.auth_service import (
        authenticate_user,
        create_or_get_google_user,
        create_session,
        create_user,
        create_password_reset_token,
        delete_session,
        get_user_by_email,
        reset_password,
    )
except ModuleNotFoundError:
    from config import settings
    from dependencies import get_current_user
    from rate_limiter import enforce_rate_limit
    from services.auth_service import (
        authenticate_user,
        create_or_get_google_user,
        create_session,
        create_user,
        create_password_reset_token,
        delete_session,
        get_user_by_email,
        reset_password,
    )


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=10)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=10)


class GoogleLoginRequest(BaseModel):
    credential: str = Field(..., min_length=10)


class PasswordResetRequest(BaseModel):
    email: str = Field(..., min_length=5)


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(..., min_length=10)
    password: str = Field(..., min_length=10)


def _serialize_user(user: dict):
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "created_at": user["created_at"],
    }


def _set_session_cookie(response: Response, token: str):
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.session_secure,
        samesite=settings.session_same_site,
        max_age=settings.session_max_age_seconds,
        path="/",
    )


@router.post("/register")
def register(data: RegisterRequest, request: Request, response: Response):
    enforce_rate_limit(request, "auth-register", limit=8, window_seconds=300)
    existing = get_user_by_email(data.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    try:
        user = create_user(data.email, data.password, data.full_name)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    token = create_session(user["id"])
    _set_session_cookie(response, token)
    return {"user": _serialize_user(user)}


@router.post("/login")
def login(data: LoginRequest, request: Request, response: Response):
    enforce_rate_limit(request, "auth-login", limit=10, window_seconds=300)
    user = authenticate_user(data.email, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_session(user["id"])
    _set_session_cookie(response, token)
    return {"user": _serialize_user(user)}


@router.post("/google")
def google_login(data: GoogleLoginRequest, request: Request, response: Response):
    enforce_rate_limit(request, "auth-google", limit=12, window_seconds=300)
    if not settings.google_client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google sign-in is not configured")
    if google_requests is None or google_id_token is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Google auth support is unavailable on the server")

    try:
        token_info = google_id_token.verify_oauth2_token(
            data.credential,
            google_requests.Request(),
            settings.google_client_id,
        )
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google credential")

    email = token_info.get("email")
    sub = token_info.get("sub")
    full_name = token_info.get("name") or email

    if not email or not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google account data is incomplete")

    user = create_or_get_google_user(email, full_name, sub)
    token = create_session(user["id"])
    _set_session_cookie(response, token)
    return {"user": _serialize_user(user)}


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return {"user": _serialize_user(current_user)}


@router.post("/logout")
def logout(
    response: Response,
    session_cookie: str | None = Cookie(default=None, alias=settings.session_cookie_name),
    current_user: dict = Depends(get_current_user),
):
    _ = current_user
    if session_cookie:
        delete_session(session_cookie)
    response.delete_cookie(key=settings.session_cookie_name, path="/")
    return {"success": True}


@router.post("/password-reset/request")
def request_password_reset(data: PasswordResetRequest, request: Request):
    enforce_rate_limit(request, "auth-password-reset", limit=6, window_seconds=300)
    token = create_password_reset_token(data.email)
    payload = {"success": True, "message": "If that account exists, a reset token has been generated."}
    if settings.debug and token:
        payload["reset_token"] = token
    return payload


@router.post("/password-reset/confirm")
def confirm_password_reset(data: PasswordResetConfirmRequest, request: Request):
    enforce_rate_limit(request, "auth-password-reset-confirm", limit=10, window_seconds=300)
    try:
        user = reset_password(data.token, data.password)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    return {"success": True, "message": "Password updated successfully"}
