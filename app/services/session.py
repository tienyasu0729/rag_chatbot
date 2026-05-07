"""
Session & Message CRUD — write-through Redis + SQL Server.

Read:  Redis first → fallback SQL Server → backfill Redis.
Write: Redis + SQL Server simultaneously. Retry queue on SQL failure.
Preferences: Redis only (ephemeral per conversation).
"""

import logging
from app.db import sqlserver
from app.db.redis_client import (
    redis_set_session_meta,
    redis_session_exists,
    redis_push_messages,
    redis_get_messages,
    redis_get_all_messages as _redis_get_all_messages,
    redis_delete_session,
    redis_delete_preferences,
    redis_track_active_session,
    redis_untrack_session,
    redis_push_pending_write,
    redis_set_preferences,
    redis_get_preferences,
    redis_get_message_count,
)

logger = logging.getLogger(__name__)


# ─── SQL (private, giữ nguyên logic cũ) ─────────────────────────


def _sql_create_session(user_id: int | None, guest_id: str | None) -> int:
    result = sqlserver.query(
        """
        INSERT INTO AIChatSessions (user_id, guest_id, started_at, last_message_at)
        OUTPUT INSERTED.id
        VALUES (@user_id, @guest_id, SYSUTCDATETIME(), SYSUTCDATETIME())
        """,
        params={"user_id": user_id, "guest_id": guest_id},
        commit=True,
    )
    return result[0]["id"]


def _sql_session_exists(session_id: int) -> bool:
    result = sqlserver.query_one(
        "SELECT id FROM AIChatSessions WHERE id = @session_id",
        params={"session_id": session_id},
    )
    return result is not None


def _sql_get_chat_history(session_id: int, limit: int) -> list[dict]:
    rows = sqlserver.query(
        """
        SELECT sender_type, content
        FROM AIChatMessages
        WHERE session_id = @session_id
        ORDER BY sent_at DESC
        OFFSET 0 ROWS FETCH NEXT @limit ROWS ONLY
        """,
        params={"session_id": session_id, "limit": limit},
    )
    return [{"role": r["sender_type"], "content": r["content"]} for r in reversed(rows)]


def _sql_save_messages(session_id: int, user_message: str, ai_reply: str):
    conn = sqlserver.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO AIChatMessages (session_id, sender_type, content, sent_at)
               VALUES (?, 'user', ?, SYSUTCDATETIME()),
                      (?, 'ai',   ?, SYSUTCDATETIME())""",
            [session_id, user_message, session_id, ai_reply],
        )
        cursor.execute(
            "UPDATE AIChatSessions SET last_message_at = SYSUTCDATETIME() WHERE id = ?",
            [session_id],
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _sql_get_all_messages(session_id: int) -> list[dict]:
    return sqlserver.query(
        """
        SELECT id, session_id, sender_type, content,
               FORMAT(sent_at, 'yyyy-MM-ddTHH:mm:ss') AS sent_at
        FROM AIChatMessages
        WHERE session_id = @session_id
        ORDER BY sent_at ASC
        """,
        params={"session_id": session_id},
    )


def _sql_get_message_count(session_id: int) -> int:
    result = sqlserver.query_one(
        "SELECT COUNT(*) AS cnt FROM AIChatMessages WHERE session_id = @session_id",
        params={"session_id": session_id},
    )
    return result["cnt"] if result else 0


def _sql_delete_session(session_id: int) -> bool:
    sqlserver.execute(
        "DELETE FROM AIChatMessages WHERE session_id = @session_id",
        params={"session_id": session_id},
    )
    affected = sqlserver.execute(
        "DELETE FROM AIChatSessions WHERE id = @session_id",
        params={"session_id": session_id},
    )
    return affected > 0


# ─── Public API (write-through) ─────────────────────────────────


def create_session(user_id: int | None = None, guest_id: str | None = None) -> int:
    session_id = _sql_create_session(user_id, guest_id)
    redis_set_session_meta(session_id, {
        "user_id": user_id or "",
        "guest_id": guest_id or "",
    })
    redis_track_active_session(session_id)
    logger.info("Created session: %d (user_id=%s, guest_id=%s)", session_id, user_id, guest_id)
    return session_id


def session_exists(session_id: int) -> bool:
    if redis_session_exists(session_id):
        return True
    return _sql_session_exists(session_id)


def get_chat_history(session_id: int, limit: int = 6) -> list[dict]:
    cached = redis_get_messages(session_id, limit)
    if cached is not None:
        return cached
    history = _sql_get_chat_history(session_id, limit)
    _backfill_redis_messages(session_id, history)
    return history


def save_messages(session_id: int, user_message: str, ai_reply: str):
    redis_push_messages(session_id, user_message, ai_reply)

    try:
        _sql_save_messages(session_id, user_message, ai_reply)
        logger.info("Saved messages for session %d", session_id)
    except Exception:
        logger.error("SQL write failed for session %d, queued for retry", session_id)
        redis_push_pending_write(session_id, user_message, ai_reply)


def get_all_messages(session_id: int) -> list[dict]:
    cached = _redis_get_all_messages(session_id)
    if cached is not None:
        return cached
    return _sql_get_all_messages(session_id)


def delete_session(session_id: int) -> bool:
    redis_delete_session(session_id)
    redis_delete_preferences(session_id)
    redis_untrack_session(session_id)
    result = _sql_delete_session(session_id)
    logger.info("Deleted session %d", session_id)
    return result


# ─── Preferences (Redis only) ───────────────────────────────────


def get_session_preferences(session_id: int) -> dict:
    return redis_get_preferences(session_id)


def save_session_preferences(session_id: int, prefs: dict):
    redis_set_preferences(session_id, prefs)


def clear_session_preferences(session_id: int):
    redis_delete_preferences(session_id)


# ─── Helpers (internal + used by sync_worker) ────────────────────


def _backfill_redis_messages(session_id: int, history: list[dict]):
    """Backfill Redis from SQL history so next read is a cache hit."""
    for msg in history:
        if msg["role"] == "user":
            user_msg = msg["content"]
        elif msg["role"] == "ai":
            redis_push_messages(session_id, user_msg, msg["content"])


def get_sql_message_count(session_id: int) -> int:
    return _sql_get_message_count(session_id)


def sql_save_messages_direct(session_id: int, user_message: str, ai_reply: str):
    """Direct SQL write — used by sync_worker for retry/reconciliation."""
    _sql_save_messages(session_id, user_message, ai_reply)
