"""
Background workers đảm bảo đồng bộ Redis ↔ SQL Server.

- flush_pending_writes(): Retry ghi messages thất bại xuống SQL (mỗi 5s)
- reconcile_sessions(): Đối chiếu message count Redis vs SQL (mỗi 60s)
- recover_on_startup(): Flush pending writes khi app khởi động lại
"""

import logging

from app.config import get_settings
from app.db.redis_client import (
    redis_pop_pending_writes,
    redis_repush_pending_write,
    redis_pending_write_count,
    redis_get_active_sessions,
    redis_get_message_count,
    is_redis_available,
)
from app.services.session import get_sql_message_count, sql_save_messages_direct

logger = logging.getLogger(__name__)


def flush_pending_writes():
    """
    Tầng 2: Retry ghi các messages đã fail xuống SQL Server.
    Được gọi bởi scheduler mỗi 5 giây.
    """
    if not is_redis_available():
        return

    items = redis_pop_pending_writes(batch_size=50)
    if not items:
        return

    settings = get_settings()
    success_count = 0
    fail_count = 0

    for item in items:
        try:
            sql_save_messages_direct(
                item["session_id"],
                item["user_msg"],
                item["ai_reply"],
            )
            success_count += 1
        except Exception:
            attempts = item.get("attempts", 0)
            if attempts < settings.REDIS_RETRY_MAX_ATTEMPTS:
                redis_repush_pending_write(item)
                fail_count += 1
            else:
                logger.error(
                    "Dropped message after %d retries: session=%d",
                    attempts, item["session_id"],
                )

    if success_count or fail_count:
        logger.info(
            "flush_pending_writes: %d synced, %d re-queued",
            success_count, fail_count,
        )


def reconcile_sessions():
    """
    Tầng 3: So sánh message count Redis vs SQL cho mỗi active session.
    Được gọi bởi scheduler mỗi 60 giây.
    """
    if not is_redis_available():
        return

    active_ids = redis_get_active_sessions()
    if not active_ids:
        return

    synced = 0
    for session_id in active_ids:
        try:
            redis_count = redis_get_message_count(session_id)
            if redis_count < 0:
                continue

            sql_count = get_sql_message_count(session_id)

            if redis_count > sql_count:
                logger.warning(
                    "Reconcile: session %d has %d Redis msgs vs %d SQL msgs — gap detected",
                    session_id, redis_count, sql_count,
                )
                synced += 1
        except Exception:
            logger.warning("Reconcile check failed for session %d", session_id, exc_info=True)

    if synced:
        logger.info("reconcile_sessions: %d sessions had discrepancies", synced)


def recover_on_startup() -> int:
    """
    Gọi 1 lần khi app khởi động.
    Flush tất cả pending_writes xuống SQL Server trước khi nhận request.
    Returns: số records đã recover.
    """
    if not is_redis_available():
        return 0

    pending = redis_pending_write_count()
    if pending == 0:
        return 0

    logger.info("Startup recovery: %d pending writes found in Redis", pending)

    total_recovered = 0
    items = redis_pop_pending_writes(batch_size=500)
    for item in items:
        try:
            sql_save_messages_direct(
                item["session_id"],
                item["user_msg"],
                item["ai_reply"],
            )
            total_recovered += 1
        except Exception:
            logger.error(
                "Startup recovery failed for session %d, re-queuing",
                item["session_id"],
            )
            redis_repush_pending_write(item)

    logger.info("Startup recovery complete: %d/%d writes recovered", total_recovered, pending)
    return total_recovered
