import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _split_csv(value: str, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    environment: str
    debug: bool
    openai_api_key: str | None
    db_path: Path
    cors_origins: list[str]
    trusted_hosts: list[str]
    session_cookie_name: str
    session_max_age_seconds: int
    session_secure: bool
    session_same_site: str
    log_level: str
    google_client_id: str | None


def get_settings() -> Settings:
    environment = os.getenv("APP_ENV", "development").strip().lower()
    debug = _as_bool(os.getenv("DEBUG"), environment != "production")
    default_db_name = "skillgenie_dev.db" if environment != "production" else "skillgenie.db"

    return Settings(
        app_name=os.getenv("APP_NAME", "SkillGenie AI"),
        environment=environment,
        debug=debug,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        db_path=Path(os.getenv("DATABASE_PATH", str(BASE_DIR / default_db_name))).resolve(),
        cors_origins=_split_csv(
            os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"),
            ["http://localhost:5173", "http://127.0.0.1:5173"],
        ),
        trusted_hosts=_split_csv(
            os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1,testserver"),
            ["localhost", "127.0.0.1", "testserver"],
        ),
        session_cookie_name=os.getenv("SESSION_COOKIE_NAME", "skillgenie_session"),
        session_max_age_seconds=int(os.getenv("SESSION_MAX_AGE_SECONDS", "604800")),
        session_secure=_as_bool(os.getenv("SESSION_COOKIE_SECURE"), environment == "production"),
        session_same_site=os.getenv("SESSION_COOKIE_SAMESITE", "lax"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        google_client_id=os.getenv("GOOGLE_CLIENT_ID"),
    )


settings = get_settings()
OPENAI_API_KEY = settings.openai_api_key
