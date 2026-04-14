try:
    from backend.database import db_cursor
except ModuleNotFoundError:
    from database import db_cursor


def _count_steps(plan_text: str) -> int:
    lines = [line.strip() for line in str(plan_text).splitlines() if line.strip()]
    weekly_steps = [line for line in lines if line.upper().startswith("WEEK ")]
    return len(weekly_steps) or len(lines) or 1


def create_learning_plan(
    user_id: int,
    role: str,
    goal: str,
    plan_text: str,
    knowledge_level: str = "beginner",
    plan_json: str | None = None,
):
    total_steps = _count_steps(plan_text)
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO learning_plans (
                user_id, role, goal, knowledge_level, plan_text, plan_json, total_steps, completed_steps, progress_percent, hours_spent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0)
            """,
            (user_id, role, goal, knowledge_level, plan_text, plan_json, total_steps),
        )
        plan_id = cursor.lastrowid
    return get_learning_plan(plan_id, user_id)


def list_learning_plans(user_id: int):
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM learning_plans
            WHERE user_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_learning_plan(plan_id: int, user_id: int):
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM learning_plans
            WHERE id = ? AND user_id = ?
            """,
            (plan_id, user_id),
        )
        row = cursor.fetchone()
    return dict(row) if row else None


def get_latest_learning_plan(user_id: int):
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM learning_plans
            WHERE user_id = ?
            ORDER BY updated_at DESC, id DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = cursor.fetchone()
    return dict(row) if row else None


def update_learning_plan_progress(user_id: int, plan_id: int, completed_steps: int, hours_spent: int):
    plan = get_learning_plan(plan_id, user_id)
    if not plan:
        return None

    total_steps = max(plan["total_steps"], 1)
    safe_completed = max(0, min(completed_steps, total_steps))
    safe_hours = max(0, hours_spent)
    percent = round((safe_completed / total_steps) * 100)

    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE learning_plans
            SET completed_steps = ?, progress_percent = ?, hours_spent = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (safe_completed, percent, safe_hours, plan_id, user_id),
        )
        cursor.execute(
            """
            INSERT INTO progress_events (user_id, learning_plan_id, completed_steps, progress_percent, hours_spent)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, plan_id, safe_completed, percent, safe_hours),
        )

    return get_learning_plan(plan_id, user_id)


def save_chat_message(user_id: int, prompt: str, response: str):
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO chat_messages (user_id, prompt, response) VALUES (?, ?, ?)",
            (user_id, prompt, response),
        )
        message_id = cursor.lastrowid
        cursor.execute("SELECT * FROM chat_messages WHERE id = ?", (message_id,))
        row = cursor.fetchone()
    return dict(row)


def list_recent_chat_messages(user_id: int, limit: int = 8):
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM chat_messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = cursor.fetchall()
    return [dict(row) for row in rows][::-1]


def get_dashboard_metrics(user_id: int):
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_plans,
                COALESCE(SUM(completed_steps), 0) AS completed_steps,
                COALESCE(SUM(total_steps), 0) AS total_steps,
                COALESCE(SUM(hours_spent), 0) AS hours_spent,
                COALESCE(MAX(progress_percent), 0) AS best_progress
            FROM learning_plans
            WHERE user_id = ?
            """,
            (user_id,),
        )
        plan_metrics = dict(cursor.fetchone())
        cursor.execute(
            "SELECT COUNT(*) AS total_messages FROM chat_messages WHERE user_id = ?",
            (user_id,),
        )
        total_messages = dict(cursor.fetchone())["total_messages"]

    total_steps = plan_metrics["total_steps"] or 0
    completed_steps = plan_metrics["completed_steps"] or 0
    focus_score = round((completed_steps / total_steps) * 100) if total_steps else 0

    return {
        "total_plans": plan_metrics["total_plans"] or 0,
        "completed_steps": completed_steps,
        "total_steps": total_steps,
        "hours_spent": plan_metrics["hours_spent"] or 0,
        "best_progress": plan_metrics["best_progress"] or 0,
        "focus_score": focus_score,
        "total_messages": total_messages or 0,
    }


def list_recent_progress_events(user_id: int, limit: int = 6):
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                progress_events.id,
                progress_events.completed_steps,
                progress_events.progress_percent,
                progress_events.hours_spent,
                progress_events.created_at,
                learning_plans.role,
                learning_plans.goal
            FROM progress_events
            JOIN learning_plans ON learning_plans.id = progress_events.learning_plan_id
            WHERE progress_events.user_id = ?
            ORDER BY progress_events.id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = cursor.fetchall()
    return [dict(row) for row in rows]
