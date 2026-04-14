import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Optional

try:
    from backend.config import settings
    from backend.database import cleanup_expired_sessions, db_cursor
except ModuleNotFoundError:
    from config import settings
    from database import cleanup_expired_sessions, db_cursor


def hash_password(password: str, salt: Optional[str] = None) -> str:
    password_salt = salt or secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        password_salt.encode("utf-8"),
        200000,
    ).hex()
    return f"{password_salt}${password_hash}"


def verify_password(password: str, password_hash: str) -> bool:
    salt, known_hash = password_hash.split("$", 1)
    candidate = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(candidate, known_hash)


def validate_password_strength(password: str):
    if len(password) < 10:
        raise ValueError("Password must be at least 10 characters long")
    if password.lower() == password or password.upper() == password:
        raise ValueError("Password must include both uppercase and lowercase letters")
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must include at least one number")


def create_user(email: str, password: str, full_name: str):
    validate_password_strength(password)
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)",
            (email.lower().strip(), hash_password(password), full_name.strip()),
        )
        user_id = cursor.lastrowid

    return get_user_by_id(user_id)


def create_google_user(email: str, full_name: str, google_sub: str):
    placeholder_password = secrets.token_urlsafe(24) + "Aa1"
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO users (email, password_hash, full_name, google_sub) VALUES (?, ?, ?, ?)",
            (email.lower().strip(), hash_password(placeholder_password), full_name.strip(), google_sub),
        )
        user_id = cursor.lastrowid
    return get_user_by_id(user_id)


def get_user_by_email(email: str):
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
        row = cursor.fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int):
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
    return dict(row) if row else None


def get_user_by_google_sub(google_sub: str):
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE google_sub = ?", (google_sub,))
        row = cursor.fetchone()
    return dict(row) if row else None


def authenticate_user(email: str, password: str):
    user = get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return user


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(user_id: int) -> str:
    cleanup_expired_sessions()
    token = secrets.token_urlsafe(48)
    token_hash = _hash_token(token)
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.session_max_age_seconds)
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO sessions (token, token_hash, user_id, created_at, expires_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
            """,
            (token, token_hash, user_id, expires_at.isoformat()),
        )
    return token


def delete_session(token: str):
    token_hash = _hash_token(token)
    with db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM sessions WHERE token_hash = ? OR token = ?", (token_hash, token))


def get_user_by_token(token: str):
    cleanup_expired_sessions()
    token_hash = _hash_token(token)
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT users.*
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE (sessions.token_hash = ? OR sessions.token = ?)
              AND (sessions.expires_at IS NULL OR datetime(sessions.expires_at) > datetime('now'))
            """,
            (token_hash, token),
        )
        row = cursor.fetchone()
    return dict(row) if row else None


def create_or_get_google_user(email: str, full_name: str, google_sub: str):
    user = get_user_by_google_sub(google_sub)
    if user:
        return user

    user = get_user_by_email(email)
    if user:
        with db_cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE users SET google_sub = ?, full_name = ? WHERE id = ?",
                (google_sub, full_name.strip() or user["full_name"], user["id"]),
            )
        return get_user_by_id(user["id"])

    return create_google_user(email, full_name, google_sub)


def create_password_reset_token(email: str):
    user = get_user_by_email(email)
    if not user:
        return None

    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(UTC) + timedelta(minutes=30)
    with db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM password_reset_tokens WHERE user_id = ?", (user["id"],))
        cursor.execute(
            """
            INSERT INTO password_reset_tokens (token_hash, user_id, expires_at)
            VALUES (?, ?, ?)
            """,
            (token_hash, user["id"], expires_at.isoformat()),
        )
    return raw_token


def reset_password(reset_token: str, new_password: str):
    validate_password_strength(new_password)
    token_hash = _hash_token(reset_token)
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id
            FROM password_reset_tokens
            WHERE token_hash = ?
              AND datetime(expires_at) > datetime('now')
            """,
            (token_hash,),
        )
        row = cursor.fetchone()

    if not row:
        return None

    user_id = row["user_id"]
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(new_password), user_id),
        )
        cursor.execute("DELETE FROM password_reset_tokens WHERE user_id = ?", (user_id,))

    return get_user_by_id(user_id)
