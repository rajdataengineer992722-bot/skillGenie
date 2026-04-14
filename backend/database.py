import sqlite3
from contextlib import contextmanager
from pathlib import Path

try:
    from backend.config import settings
except ModuleNotFoundError:
    from config import settings


DB_PATH = Path(settings.db_path)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=MEMORY")
    connection.execute("PRAGMA temp_store=MEMORY")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


@contextmanager
def db_cursor(commit=False):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        yield cursor
        if commit:
            connection.commit()
    finally:
        connection.close()


def init_db():
    with db_cursor(commit=True) as cursor:
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS learning_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                goal TEXT NOT NULL,
                knowledge_level TEXT NOT NULL DEFAULT 'beginner',
                plan_text TEXT NOT NULL,
                plan_json TEXT,
                total_steps INTEGER NOT NULL DEFAULT 0,
                completed_steps INTEGER NOT NULL DEFAULT 0,
                progress_percent INTEGER NOT NULL DEFAULT 0,
                hours_spent INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                prompt TEXT NOT NULL,
                response TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS progress_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                learning_plan_id INTEGER NOT NULL,
                completed_steps INTEGER NOT NULL,
                progress_percent INTEGER NOT NULL,
                hours_spent INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (learning_plan_id) REFERENCES learning_plans(id) ON DELETE CASCADE
            );
            """
        )
        cursor.execute("PRAGMA table_info(sessions)")
        columns = {row["name"] for row in cursor.fetchall()}
        if "token_hash" not in columns:
            cursor.execute("ALTER TABLE sessions ADD COLUMN token_hash TEXT")
        if "expires_at" not in columns:
            cursor.execute("ALTER TABLE sessions ADD COLUMN expires_at TIMESTAMP")
        cursor.execute("PRAGMA table_info(users)")
        user_columns = {row["name"] for row in cursor.fetchall()}
        if "google_sub" not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN google_sub TEXT")
        cursor.execute("PRAGMA table_info(learning_plans)")
        learning_plan_columns = {row["name"] for row in cursor.fetchall()}
        if "knowledge_level" not in learning_plan_columns:
            cursor.execute("ALTER TABLE learning_plans ADD COLUMN knowledge_level TEXT NOT NULL DEFAULT 'beginner'")
        if "plan_json" not in learning_plan_columns:
            cursor.execute("ALTER TABLE learning_plans ADD COLUMN plan_json TEXT")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_sub ON users(google_sub)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_learning_plans_user_id ON learning_plans(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress_events_plan_id ON progress_events(learning_plan_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_password_reset_user_id ON password_reset_tokens(user_id)")


def cleanup_expired_sessions():
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            DELETE FROM sessions
            WHERE expires_at IS NOT NULL AND datetime(expires_at) <= datetime('now')
            """
        )
