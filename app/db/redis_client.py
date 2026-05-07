"""
Redis client singleton + helper functions.
Write-through cache layer cho session/messages/preferences.
"""

import json
import logging
import time
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError, RedisError

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: Redis | None = None
_available: bool = False

# ─── Core ────────────────────────────────────────────────────────


def get_redis_client() -> Redis | None:
    global _client, _available
    if _client is None:
        settings = get_settings()
        try:
            _client = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3,
            )
            _client.ping()
            _available = True
        except (RedisConnectionError, RedisError):
            logger.warning("Redis connection failed")
            _client = None
            _available = False
    return _client


def init_redis() -> bool:
    client = get_redis_client()
    if client:
        logger.info("Redis connected: %s:%s", get_settings().REDIS_HOST, get_settings().REDIS_PORT)
        return True
    logger.warning("Redis unavailable, falling back to SQL Server only")
    return False


def is_redis_available() -> bool:
    global _available
    if not _available or _client is None:
        return False
    try:
        _client.ping()
        return True
    except (RedisConnectionError, RedisError):
        _available = False
        return False


def _safe(func):
    """Decorator: catch Redis errors, return fallback value."""
    def wrapper(*args, **kwargs):
        if not is_redis_available():
            return kwargs.get("_fallback")
        try:
            return func(*args, **kwargs)
        except (RedisConnectionError, RedisError):
            logger.warning("Redis operation failed: %s", func.__name__, exc_info=True)
            return kwargs.get("_fallback")
    return wrapper


def _key(session_id: int, suffix: str) -> str:
    return f"session:{session_id}:{suffix}"


def _ttl() -> int:
    return get_settings().REDIS_SESSION_TTL


# ─── Session meta ────────────────────────────────────────────────


def redis_set_session_meta(session_id: int, meta: dict) -> bool:
    if not is_redis_available():
        return False
    try:
        key = _key(session_id, "meta")
        _client.hset(key, mapping={k: str(v) if v is not None else "" for k, v in meta.items()})
        _client.expire(key, _ttl())
        return True
    except (RedisConnectionError, RedisError):
        logger.warning("redis_set_session_meta failed for session %d", session_id)
        return False


def redis_get_session_meta(session_id: int) -> dict | None:
    if not is_redis_available():
        return None
    try:
        data = _client.hgetall(_key(session_id, "meta"))
        return data if data else None
    except (RedisConnectionError, RedisError):
        return None


def redis_session_exists(session_id: int) -> bool:
    if not is_redis_available():
        return False
    try:
        return _client.exists(_key(session_id, "meta")) > 0
    except (RedisConnectionError, RedisError):
        return False


# ─── Messages ────────────────────────────────────────────────────


def redis_push_messages(session_id: int, user_msg: str, ai_reply: str) -> bool:
    if not is_redis_available():
        return False
    try:
        key = _key(session_id, "messages")
        now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        pipe = _client.pipeline()
        pipe.rpush(key, json.dumps({
            "role": "user", "sender_type": "user",
            "session_id": session_id,
            "content": user_msg, "sent_at": now,
        }, ensure_ascii=False))
        pipe.rpush(key, json.dumps({
            "role": "ai", "sender_type": "ai",
            "session_id": session_id,
            "content": ai_reply, "sent_at": now,
        }, ensure_ascii=False))
        pipe.expire(key, _ttl())
        meta_key = _key(session_id, "meta")
        pipe.hset(meta_key, "last_message_at", now)
        pipe.execute()
        return True
    except (RedisConnectionError, RedisError):
        logger.warning("redis_push_messages failed for session %d", session_id)
        return False


def _normalize_message(msg: dict, session_id: int) -> dict:
    """Ensure message dict has all required fields, handling legacy data."""
    msg.setdefault("session_id", session_id)
    msg.setdefault("sender_type", msg.get("role", "user"))
    msg.setdefault("id", 0)
    return msg


def redis_get_messages(session_id: int, limit: int) -> list[dict] | None:
    """Return last `limit` messages chronologically, or None on miss/error."""
    if not is_redis_available():
        return None
    try:
        key = _key(session_id, "messages")
        if not _client.exists(key):
            return None
        raw = _client.lrange(key, -limit, -1)
        return [_normalize_message(json.loads(r), session_id) for r in raw]
    except (RedisConnectionError, RedisError):
        return None


def redis_get_all_messages(session_id: int) -> list[dict] | None:
    if not is_redis_available():
        return None
    try:
        key = _key(session_id, "messages")
        if not _client.exists(key):
            return None
        raw = _client.lrange(key, 0, -1)
        return [_normalize_message(json.loads(r), session_id) for r in raw]
    except (RedisConnectionError, RedisError):
        return None


def redis_get_message_count(session_id: int) -> int:
    if not is_redis_available():
        return -1
    try:
        return _client.llen(_key(session_id, "messages"))
    except (RedisConnectionError, RedisError):
        return -1


def redis_delete_session(session_id: int) -> bool:
    if not is_redis_available():
        return False
    try:
        _client.delete(
            _key(session_id, "meta"),
            _key(session_id, "messages"),
            _key(session_id, "preferences"),
        )
        return True
    except (RedisConnectionError, RedisError):
        return False


# ─── Preferences ─────────────────────────────────────────────────


def redis_set_preferences(session_id: int, prefs: dict) -> bool:
    if not is_redis_available():
        return False
    try:
        key = _key(session_id, "preferences")
        _client.set(key, json.dumps(prefs, ensure_ascii=False))
        _client.expire(key, _ttl())
        return True
    except (RedisConnectionError, RedisError):
        return False


def redis_get_preferences(session_id: int) -> dict:
    if not is_redis_available():
        return {}
    try:
        raw = _client.get(_key(session_id, "preferences"))
        return json.loads(raw) if raw else {}
    except (RedisConnectionError, RedisError):
        return {}


def redis_delete_preferences(session_id: int) -> bool:
    if not is_redis_available():
        return False
    try:
        _client.delete(_key(session_id, "preferences"))
        return True
    except (RedisConnectionError, RedisError):
        return False


# ─── Sync / Retry queue ─────────────────────────────────────────

_PENDING_KEY = "sync:pending_writes"


def redis_push_pending_write(session_id: int, user_msg: str, ai_reply: str) -> bool:
    if not is_redis_available():
        return False
    try:
        payload = json.dumps({
            "session_id": session_id,
            "user_msg": user_msg,
            "ai_reply": ai_reply,
            "timestamp": time.time(),
            "attempts": 0,
        }, ensure_ascii=False)
        _client.rpush(_PENDING_KEY, payload)
        return True
    except (RedisConnectionError, RedisError):
        return False


def redis_pop_pending_writes(batch_size: int = 50) -> list[dict]:
    if not is_redis_available():
        return []
    try:
        items = []
        for _ in range(batch_size):
            raw = _client.lpop(_PENDING_KEY)
            if raw is None:
                break
            items.append(json.loads(raw))
        return items
    except (RedisConnectionError, RedisError):
        return []


def redis_repush_pending_write(item: dict) -> bool:
    """Put a failed item back into the queue with incremented attempt count."""
    if not is_redis_available():
        return False
    try:
        item["attempts"] = item.get("attempts", 0) + 1
        _client.rpush(_PENDING_KEY, json.dumps(item, ensure_ascii=False))
        return True
    except (RedisConnectionError, RedisError):
        return False


def redis_pending_write_count() -> int:
    if not is_redis_available():
        return 0
    try:
        return _client.llen(_PENDING_KEY)
    except (RedisConnectionError, RedisError):
        return 0


# ─── Active sessions tracking ───────────────────────────────────

_ACTIVE_KEY = "sync:active_sessions"


def redis_track_active_session(session_id: int) -> bool:
    if not is_redis_available():
        return False
    try:
        _client.sadd(_ACTIVE_KEY, str(session_id))
        return True
    except (RedisConnectionError, RedisError):
        return False


def redis_get_active_sessions() -> set[int]:
    if not is_redis_available():
        return set()
    try:
        members = _client.smembers(_ACTIVE_KEY)
        return {int(m) for m in members}
    except (RedisConnectionError, RedisError):
        return set()


def redis_untrack_session(session_id: int) -> bool:
    if not is_redis_available():
        return False
    try:
        _client.srem(_ACTIVE_KEY, str(session_id))
        return True
    except (RedisConnectionError, RedisError):
        return False
