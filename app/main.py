"""
FastAPI application — RAG Chatbot tư vấn xe hơi.
"""

import json
import logging
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import get_settings
from app.db.qdrant import (
    init_collection,
    is_qdrant_available,
    get_qdrant_status,
    QdrantUnavailableError,
)
from app.db.redis_client import init_redis, is_redis_available
from app.services import embedding as embedding_service
from app.services.intent import classify_intent
from app.services.rag import rag_search
from app.services.database_query import (
    count_vehicles,
    get_inventory_snapshot,
    format_stats_header,
    format_filtered_count,
)
from app.services.mcp_dispatcher import dispatch as mcp_dispatch
from app.services.mcp_logging import get_mcp_stats
from app.services.preference import extract_preferences, merge_preferences, format_preferences_summary
from app.services.session import (
    create_session,
    session_exists,
    get_chat_history,
    save_messages,
    get_all_messages,
    delete_session,
    get_session_preferences,
    save_session_preferences,
)
from app.services.sync_worker import recover_on_startup, flush_pending_writes, reconcile_sessions
from app.services.llm import chat_completion, check_health as llm_check_health
from app.pipeline.sync import sync_all_vehicles, sync_changed_vehicles, sync_vehicles_if_changed
from app.routes.internal_pricing_router import router as internal_pricing_router
from app.routes.pricing_reference_router import router as pricing_reference_router
from app.routes.pricing_router import router as pricing_router
from app.models.schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    SendMessageRequest,
    SendMessageResponse,
    ChatMessageOut,
    SyncResponse,
    MCPStatsResponse,
)

# ─── Logging ─────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)

# ─── Scheduler ───────────────────────────────────────────────────

scheduler = BackgroundScheduler()
startup_sync_status = {
    "ok": True,
    "error": None,
}


def _qdrant_error_detail() -> str:
    status = get_qdrant_status()
    return status["last_error"] or "Qdrant chưa sẵn sàng"


def _require_qdrant() -> None:
    if is_qdrant_available():
        return
    raise HTTPException(
        status_code=503,
        detail=f"Dịch vụ tìm kiếm vector đang tạm thời không khả dụng: {_qdrant_error_detail()}",
    )


def _scheduled_sync():
    """Background sync job — incremental khi có thể, full khi cần."""
    try:
        logger.info("Scheduled sync starting...")
        count = sync_changed_vehicles()
        logger.info("Scheduled sync complete: %d vehicles", count)
    except Exception:
        logger.exception("Scheduled sync failed")


# ─── Lifespan ────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # 1. Load embedding service
    logger.info("Loading embedding service...")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        embedding_service.load_model,
        settings.EMBEDDING_MODEL,
    )

    # 2. Init Qdrant collection
    logger.info("Initializing Qdrant collection...")
    try:
        init_collection()
    except QdrantUnavailableError as exc:
        logger.warning("Qdrant unavailable at startup; continue in degraded mode: %s", exc)

    # 3. Init Redis + startup recovery
    redis_ok = init_redis()
    if redis_ok:
        recovered = recover_on_startup()
        if recovered:
            logger.info("Recovered %d pending writes from Redis", recovered)
        scheduler.add_job(
            flush_pending_writes, "interval",
            seconds=settings.REDIS_RETRY_INTERVAL, id="redis_retry",
        )
        scheduler.add_job(
            reconcile_sessions, "interval",
            seconds=settings.REDIS_RECONCILE_INTERVAL, id="redis_reconcile",
        )

    # 4. Startup sync theo delta, tránh full re-embed khi restart
    logger.info("Running startup delta sync...")
    try:
        await loop.run_in_executor(None, sync_vehicles_if_changed)
        startup_sync_status["ok"] = True
        startup_sync_status["error"] = None
    except Exception as exc:
        startup_sync_status["ok"] = False
        startup_sync_status["error"] = str(exc)
        logger.exception("Startup delta sync failed; continue in degraded mode")

    # 5. Start scheduler
    scheduler.add_job(
        _scheduled_sync,
        "interval",
        minutes=settings.SYNC_INTERVAL_MINUTES,
        id="vehicle_sync",
    )
    scheduler.start()
    logger.info("Scheduler started: sync every %d minutes", settings.SYNC_INTERVAL_MINUTES)

    yield

    scheduler.shutdown(wait=False)
    logger.info("Application shutdown")


# ─── FastAPI App ─────────────────────────────────────────────────

app = FastAPI(
    title="RAG Chatbot - Tư vấn xe hơi",
    description="Chatbot tư vấn xe hơi sử dụng RAG + Text-to-SQL + Tư vấn cá nhân hóa",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pricing_router)
app.include_router(internal_pricing_router)
app.include_router(pricing_reference_router)

# ─── Prompts theo intent ─────────────────────────────────────────

PROMPTS = {
    "RAG": """Bạn là nhân viên tư vấn xe chuyên nghiệp tại showroom ô tô, tên là Minh.

PHONG CÁCH GIAO TIẾP:
- Tiếng Việt tự nhiên, thân thiện, như nói chuyện trực tiếp
- Xưng "em", gọi khách "anh/chị"
- Không liệt kê bullet point máy móc, viết thành câu văn mạch lạc
- Kết thúc bằng 1 câu hỏi gợi mở
- Nếu không có xe phù hợp, nói thẳng và đề xuất tiêu chí khác

RÀNG BUỘC:
- Chỉ tư vấn dựa trên thông tin trong context bên dưới
- Không bịa đặt thông số, giá, màu sắc không có trong dữ liệu
- Không nhắc đến xe không xuất hiện trong context

QUY TẮC TOÀN VẸN SỐ LIỆU:
- Tất cả con số về số lượng xe (tổng số, số xe theo hãng/loại...) CHỈ được lấy từ phần [THỐNG KÊ THẬT TỪ DATABASE] trong context.
- TUYỆT ĐỐI KHÔNG đếm số item trong phần [MẪU TIÊU BIỂU] rồi dùng làm tổng.
- Nếu thống kê ghi "Tổng: 85 xe" nhưng mẫu chỉ có 5 xe, phải nói "có 85 xe, dưới đây là một số xe tiêu biểu".
- Nếu không có phần [THỐNG KÊ THẬT TỪ DATABASE], phải nói rõ "em đang xem một phần dữ liệu" thay vì đưa ra con số tổng.

{context_section}

Lịch sử hội thoại:
{history}

Câu hỏi của khách: {query}""",

    "RECOMMEND": """Bạn là Minh — nhân viên tư vấn xe có 5 năm kinh nghiệm, đang tư vấn trực tiếp.

THÔNG TIN VỀ KHÁCH HÀNG (đã trích xuất từ hội thoại):
{preferences_summary}

XE PHÙ HỢP HIỆN CÓ TẠI SHOWROOM:
{context_section}

NHIỆM VỤ:
1. Giới thiệu 2-3 xe phù hợp nhất với nhu cầu của khách — nêu rõ TẠI SAO phù hợp với TỪNG tiêu chí của họ
2. So sánh ngắn gọn ưu/nhược điểm của mỗi lựa chọn
3. Đặt 1 câu hỏi để hiểu thêm (nếu còn thiếu thông tin quan trọng)

PHONG CÁCH: Tiếng Việt tự nhiên, thân thiện. Không liệt kê bullet point máy móc.
RÀNG BUỘC: Chỉ nhắc xe có trong danh sách trên. Không bịa thông số.
- Nếu khách đã từ chối cung cấp thêm thông tin hoặc yêu cầu tìm ngay → TUYỆT ĐỐI không hỏi thêm, giới thiệu xe luôn với dữ liệu hiện có.

QUY TẮC TOÀN VẸN SỐ LIỆU:
- Tất cả con số về số lượng xe CHỈ được lấy từ phần [THỐNG KÊ THẬT TỪ DATABASE] trong context.
- TUYỆT ĐỐI KHÔNG đếm số item trong phần [MẪU TIÊU BIỂU] rồi dùng làm tổng.
- Nếu thống kê ghi "Tổng: N xe" nhưng mẫu chỉ có vài xe, phải nói "có N xe phù hợp, dưới đây là một số xe tiêu biểu".
- Nếu không có phần [THỐNG KÊ THẬT TỪ DATABASE], phải nói rõ "em đang xem một phần dữ liệu" thay vì đưa ra con số tổng.

Lịch sử hội thoại:
{history}

Tin nhắn hiện tại: {query}""",

    "CLARIFY": """Bạn là Minh — nhân viên tư vấn xe, đang nói chuyện trực tiếp với khách.

Khách vừa nói: "{query}"
Thông tin đã biết về khách: {preferences_summary}

CÁCH TRẢ LỜI:
- Xưng "em", gọi khách "anh/chị"
- Viết 1-2 câu ngắn gọn, tự nhiên như đang trò chuyện — KHÔNG dùng heading in đậm, KHÔNG dùng bullet point, KHÔNG liệt kê ưu tiên
- Chỉ hỏi đúng 1 câu duy nhất, lồng tự nhiên vào câu nói, ví dụ: "Dạ em ghi nhận rồi ạ. Anh/chị dùng xe chủ yếu đi trong thành phố hay đường trường ạ?"
- Nếu chưa biết ngân sách thì hỏi ngân sách trước. Nếu đã có ngân sách thì hỏi mục đích sử dụng.

TUYỆT ĐỐI KHÔNG LÀM:
- Không viết "Xác nhận thông tin:", "Câu hỏi quan trọng:", hay bất kỳ heading nào
- Không liệt kê nhiều câu hỏi
- Nếu khách tỏ ý muốn tìm ngay, từ chối cung cấp thêm, hoặc nói đại ý "tìm giúp tôi đi" → DỪNG hỏi, trả lời rằng em sẽ tìm ngay với thông tin hiện có

Lịch sử hội thoại:
{history}""",

    "SQL": """Bạn là Minh — nhân viên tư vấn xe tại showroom.

Khách vừa hỏi một câu thống kê. Đây là kết quả từ hệ thống:
{context_section}

Hãy trình bày kết quả bằng tiếng Việt tự nhiên, dễ hiểu.
Nếu kết quả rỗng hoặc không phù hợp, giải thích lịch sự và gợi ý cách hỏi khác.

QUY TẮC TOÀN VẸN SỐ LIỆU:
- Tất cả con số về số lượng xe CHỈ được lấy từ phần [THỐNG KÊ THẬT TỪ DATABASE] hoặc kết quả thống kê trong context.
- KHÔNG tự bịa hoặc ước lượng con số nếu context không cung cấp.

Lịch sử hội thoại:
{history}

Câu hỏi của khách: {query}""",

    "OTHER": """Bạn là Minh — nhân viên tư vấn xe tại showroom ô tô.
Khách đang hỏi ngoài phạm vi tư vấn xe.
Hãy trả lời lịch sự, ngắn gọn, rồi gợi ý quay lại chủ đề xe.
Không từ chối cứng nhắc, chỉ hướng dẫn nhẹ nhàng.

Lịch sử hội thoại:
{history}

Tin nhắn của khách: {query}""",
}


# ─── Helpers ─────────────────────────────────────────────────────

def _build_context_section(
    intent: str,
    rag_results: list[str] | None,
    sql_result: dict | None,
    stats_header: str = "",
    filtered_count_line: str = "",
) -> str:
    parts: list[str] = []

    if stats_header:
        parts.append(stats_header)

    if filtered_count_line:
        parts.append(filtered_count_line)

    if intent == "RECOMMEND":
        if rag_results:
            texts = "\n---\n".join(rag_results)
            parts.append(f"[MẪU TIÊU BIỂU ĐỂ GIỚI THIỆU]\n---\n{texts}")
        else:
            parts.append("Không tìm thấy xe phù hợp với tiêu chí hiện tại. Hãy gợi ý khách điều chỉnh ngân sách hoặc tiêu chí.")
        return "\n\n".join(parts)

    if intent == "CLARIFY":
        return ""

    if intent == "RAG":
        if rag_results:
            texts = "\n---\n".join(rag_results)
            parts.append(f"[MẪU TIÊU BIỂU ĐỂ GIỚI THIỆU]\n---\n{texts}")
        else:
            parts.append("Không tìm thấy xe phù hợp trong kho. Hãy thông báo cho khách và gợi ý tiêu chí khác.")
        return "\n\n".join(parts)

    if intent == "SQL":
        if sql_result and sql_result.get("results") is not None:
            parts.append(f"Kết quả thống kê từ hệ thống:\n{json.dumps(sql_result['results'], ensure_ascii=False, indent=2, default=str)}")
        else:
            parts.append("Không có kết quả thống kê phù hợp.")
        return "\n\n".join(parts)

    return "Khách đang hỏi ngoài phạm vi tư vấn xe. Trả lời lịch sự và gợi ý quay lại chủ đề xe."


def _format_history(history: list[dict]) -> str:
    if not history:
        return "(Chưa có lịch sử)"
    lines = []
    for msg in history:
        role = "Khách" if msg["role"] == "user" else "Tư vấn viên"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def _need_more_info(prefs: dict) -> bool:
    """Trả về True khi KHÔNG có bất kỳ tiêu chí lọc nào — cần hỏi thêm."""
    if not prefs:
        return True
    filterable_keys = (
        "ngan_sach_max", "ngan_sach_min", "muc_dich",
        "nhien_lieu", "hop_so", "hang_xe_yeu_thich", "so_cho",
    )
    return not any(prefs.get(k) is not None for k in filterable_keys)


def _generate_suggested_questions(intent: str, preferences: dict, vehicle_ids: list[int]) -> list[str]:
    questions = []

    if intent == "RECOMMEND" and vehicle_ids:
        questions.append("So sánh chi tiết các xe này cho em")
        if not preferences.get("ngan_sach_max"):
            questions.append("Xe nào dưới 400 triệu phù hợp không?")
        questions.append("Đặt lịch xem xe trực tiếp được không?")

    elif intent == "RAG":
        questions.append("Xe này còn màu nào?")
        questions.append("Chi phí bảo dưỡng hàng năm khoảng bao nhiêu?")
        questions.append("Có xe tương tự giá rẻ hơn không?")

    elif intent == "CLARIFY":
        if not preferences.get("ngan_sach_max"):
            questions.append("Khoảng 400-500 triệu")
            questions.append("Khoảng 600-800 triệu")
            questions.append("Trên 800 triệu")
        elif not preferences.get("muc_dich"):
            questions.append("Chủ yếu đi trong thành phố")
            questions.append("Đi đường trường là chính")
            questions.append("Cần xe cho gia đình")
        else:
            questions.append("Cần xe tiết kiệm nhiên liệu")
            questions.append("Ưu tiên nội thất rộng rãi")
            questions.append("Cần xe tự động, dễ lái")

    elif intent == "SQL":
        questions.append("Xe nào rẻ nhất hiện tại?")
        questions.append("Có bao nhiêu xe còn trong kho?")

    elif intent == "OTHER":
        questions.append("Tư vấn xe cho tôi")
        questions.append("Xe nào phù hợp gia đình?")
        questions.append("Xe dưới 500 triệu có những loại nào?")

    return questions[:3]


# ─── DB Stats Helpers ────────────────────────────────────────────

import re as _re

_BRAND_PATTERN = _re.compile(
    r"(toyota|honda|ford|mazda|hyundai|kia|mitsubishi|suzuki|nissan"
    r"|vinfast|mercedes|bmw|audi|lexus|peugeot|chevrolet|isuzu"
    r"|subaru|volvo|mg|haval|chery|wuling)",
    _re.IGNORECASE,
)


def _extract_brand_keyword(message: str, preferences: dict | None = None) -> str | None:
    """Heuristic: lấy tên hãng xe từ message hoặc preferences."""
    if preferences and preferences.get("hang_xe_yeu_thich"):
        return preferences["hang_xe_yeu_thich"]
    m = _BRAND_PATTERN.search(message)
    return m.group(1) if m else None


def _safe_stats_header() -> str:
    """Gọi get_inventory_snapshot, trả về header hoặc chuỗi rỗng nếu lỗi."""
    try:
        return format_stats_header(get_inventory_snapshot())
    except Exception:
        logger.warning("Failed to get inventory snapshot", exc_info=True)
        return ""


def _get_vehicle_stats(
    preferences: dict | None,
    message: str,
) -> tuple[str, str]:
    """
    Returns (filtered_count_line, stats_header).
    filtered_count_line: dòng COUNT có điều kiện theo brand/preferences.
    stats_header: thống kê tổng quan toàn kho.
    """
    stats_header = _safe_stats_header()

    brand = _extract_brand_keyword(message, preferences)
    count_kwargs: dict = {}
    label_parts: list[str] = []

    if brand:
        count_kwargs["title_keyword"] = brand
        label_parts.append(f"xe {brand}")

    if preferences:
        if preferences.get("nhien_lieu"):
            count_kwargs["fuel"] = preferences["nhien_lieu"]
        if preferences.get("hop_so"):
            count_kwargs["transmission"] = preferences["hop_so"]
        if preferences.get("ngan_sach_min") is not None:
            count_kwargs["budget_min"] = preferences["ngan_sach_min"]
        if preferences.get("ngan_sach_max") is not None:
            count_kwargs["budget_max"] = preferences["ngan_sach_max"]

    if not count_kwargs:
        return "", stats_header

    try:
        cnt = count_vehicles(**count_kwargs)
        label = " ".join(label_parts) if label_parts else "xe phù hợp tiêu chí"
        return format_filtered_count(cnt, label), stats_header
    except Exception:
        logger.warning("Failed to count vehicles", exc_info=True)
        return "", stats_header


def _try_db_count_fallback(message: str, preferences: dict | None) -> list[dict] | None:
    """Khi SQL agent fail, thử đếm bằng DatabaseQueryService cho pattern đơn giản."""
    brand = _extract_brand_keyword(message, preferences)
    if not brand:
        return None
    try:
        cnt = count_vehicles(title_keyword=brand)
        return [{"so_luong": cnt, "dieu_kien": f"xe {brand} đang bán"}]
    except Exception:
        logger.warning("DB count fallback failed", exc_info=True)
        return None


# ─── API Endpoints ───────────────────────────────────────────────

@app.post("/ai-chat/sessions", response_model=CreateSessionResponse)
async def api_create_session(req: CreateSessionRequest):
    """Tạo session mới."""
    user_id = req.user_id if req.user_id else None
    guest_id = req.guest_id or None

    if not user_id and not guest_id:
        raise HTTPException(status_code=400, detail="Cần có user_id hoặc guest_id")

    try:
        session_id = create_session(user_id=user_id, guest_id=guest_id)
        return CreateSessionResponse(session_id=session_id)
    except Exception:
        logger.exception("Error creating session")
        raise HTTPException(status_code=500, detail="Lỗi hệ thống, vui lòng thử lại")


@app.post("/ai-chat/sessions/{session_id}/messages", response_model=SendMessageResponse)
async def api_send_message(session_id: int, req: SendMessageRequest):
    """Gửi tin nhắn và nhận phản hồi từ chatbot."""

    if not embedding_service.is_ready():
        raise HTTPException(status_code=503, detail="Hệ thống đang khởi động, vui lòng thử lại sau")

    if not session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session không tồn tại, vui lòng tạo session mới")

    settings = get_settings()

    try:
        # [1] Lấy lịch sử
        history = get_chat_history(session_id, limit=settings.MAX_HISTORY_TURNS)

        # [2] Phân loại intent
        intent = classify_intent(req.message, history)

        # [2.5] Lấy preferences từ Redis
        preferences = get_session_preferences(session_id)

        # [3] Xử lý theo intent
        rag_results = None
        sql_result = None
        vehicle_ids: list[int] = []
        stats_header = ""
        filtered_count_line = ""

        if intent in ("RECOMMEND", "CLARIFY"):
            new_prefs = extract_preferences(history, req.message)
            preferences = merge_preferences(preferences, new_prefs)
            save_session_preferences(session_id, preferences)

            if not _need_more_info(preferences):
                intent = "RECOMMEND"
                _require_qdrant()
                rag_results, vehicle_ids = rag_search(req.message, preferences=preferences)
                filtered_count_line, stats_header = _get_vehicle_stats(
                    preferences, req.message,
                )
            elif intent == "RECOMMEND":
                _require_qdrant()
                rag_results, vehicle_ids = rag_search(req.message, preferences=preferences)
                filtered_count_line, stats_header = _get_vehicle_stats(
                    preferences, req.message,
                )
                if not rag_results:
                    intent = "CLARIFY"
            # else: intent stays CLARIFY — no filterable criteria at all

        elif intent == "RAG":
            _require_qdrant()
            rag_results, vehicle_ids = rag_search(req.message, preferences=preferences)
            filtered_count_line, stats_header = _get_vehicle_stats(
                preferences, req.message,
            )

        elif intent == "SQL":
            sql_result = mcp_dispatch(
                req.message,
                history,
                preferences=preferences,
                db_fallback_fn=_try_db_count_fallback,
                session_id=session_id,
            )
            if not sql_result["success"]:
                logger.warning("MCP/SQL flow empty, falling back to RAG")
                intent = "RAG"
                _require_qdrant()
                rag_results, vehicle_ids = rag_search(req.message)
            stats_header = _safe_stats_header()

        # [4] Build prompt theo intent
        preferences_summary = format_preferences_summary(preferences) if preferences else "(Chưa có thông tin)"
        context_section = _build_context_section(
            intent, rag_results, sql_result,
            stats_header=stats_header,
            filtered_count_line=filtered_count_line,
        )
        history_text = _format_history(history)

        prompt_template = PROMPTS.get(intent, PROMPTS["OTHER"])
        prompt = prompt_template.format(
            context_section=context_section,
            history=history_text,
            query=req.message,
            preferences_summary=preferences_summary,
        )

        reply = chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1024,
        )

        # [5] Lưu hội thoại (write-through: Redis + SQL Server)
        save_messages(session_id, req.message, reply)

        # [6] Suggested questions (rule-based)
        suggested = _generate_suggested_questions(intent, preferences, vehicle_ids)

        # [7] Response
        return SendMessageResponse(
            reply=reply,
            intent=intent,
            session_id=session_id,
            vehicle_ids=vehicle_ids,
            suggested_questions=suggested,
            preferences_snapshot=preferences or {},
        )

    except HTTPException:
        raise
    except QdrantUnavailableError:
        raise HTTPException(
            status_code=503,
            detail=f"Dịch vụ tìm kiếm vector đang tạm thời không khả dụng: {_qdrant_error_detail()}",
        )
    except Exception as exc:
        logger.exception("Error processing message (session=%d)", session_id)
        err_str = str(exc)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "No healthy" in err_str:
            raise HTTPException(
                status_code=429,
                detail="LLM API tạm thời hết quota, vui lòng thử lại sau."
            )
        raise HTTPException(status_code=503, detail="Hệ thống tạm thời gặp sự cố, vui lòng thử lại sau")


@app.get("/ai-chat/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
async def api_get_messages(session_id: int):
    """Lấy lịch sử hội thoại."""
    if not session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session không tồn tại")

    try:
        rows = get_all_messages(session_id)
        return [
            ChatMessageOut(
                id=r.get("id", 0),
                session_id=r.get("session_id", session_id),
                sender_type=r.get("sender_type", r.get("role", "user")),
                content=r["content"],
                sent_at=r["sent_at"],
            )
            for r in rows
        ]
    except Exception:
        logger.exception("Error getting messages (session=%d)", session_id)
        raise HTTPException(status_code=500, detail="Lỗi hệ thống")


@app.delete("/ai-chat/sessions/{session_id}")
async def api_delete_session(session_id: int):
    """Xóa session (cascade xóa messages)."""
    if not session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session không tồn tại")

    try:
        delete_session(session_id)
        return {"status": "deleted", "session_id": session_id}
    except Exception:
        logger.exception("Error deleting session %d", session_id)
        raise HTTPException(status_code=500, detail="Lỗi hệ thống")


@app.post("/admin/ai-chat/sync-embeddings", response_model=SyncResponse)
async def api_sync_embeddings(
    background_tasks: BackgroundTasks,
    x_admin_key: str = Header(..., alias="X-Admin-Key"),
):
    """Kích hoạt pipeline đồng bộ toàn bộ (admin only)."""
    settings = get_settings()

    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="API key không hợp lệ")

    if not embedding_service.is_ready():
        raise HTTPException(status_code=503, detail="Embedding service chưa sẵn sàng")
    if not is_qdrant_available():
        raise HTTPException(
            status_code=503,
            detail=f"Qdrant chưa sẵn sàng để đồng bộ embeddings: {_qdrant_error_detail()}",
        )

    background_tasks.add_task(_run_sync_background)
    return SyncResponse(
        status="started",
        message="Pipeline đồng bộ đã được kích hoạt",
    )


@app.get("/admin/mcp/stats", response_model=MCPStatsResponse)
async def api_mcp_stats(
    x_admin_key: str = Header(..., alias="X-Admin-Key"),
):
    """Thống kê hiệu quả MCP dispatcher."""
    settings = get_settings()

    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="API key không hợp lệ")

    try:
        return MCPStatsResponse(**get_mcp_stats(days=7))
    except Exception:
        logger.exception("Error getting MCP stats")
        raise HTTPException(status_code=500, detail="Lỗi hệ thống")


async def _run_sync_background():
    try:
        loop = asyncio.get_event_loop()
        count = await loop.run_in_executor(None, sync_all_vehicles)
        logger.info("Admin sync complete: %d vehicles", count)
    except Exception:
        logger.exception("Admin sync failed")


# ─── Chat UI (test) ──────────────────────────────────────────────

@app.get("/chat")
async def chat_ui():
    """Serve chat UI cho test."""
    html_path = Path(__file__).resolve().parent.parent / "test_chat.html"
    return FileResponse(html_path, media_type="text/html")


@app.get("/pricing-ui")
async def pricing_ui():
    """Serve pricing UI template cho test tính năng định giá xe."""
    html_path = Path(__file__).resolve().parent.parent / "test_pricing.html"
    return FileResponse(html_path, media_type="text/html")


# ─── Health check ────────────────────────────────────────────────

@app.get("/health")
async def health():
    qdrant_status = get_qdrant_status()
    degraded = (not startup_sync_status["ok"]) or (not qdrant_status["available"])
    return {
        "status": "ok" if not degraded else "degraded",
        "embedding_ready": embedding_service.is_ready(),
        "qdrant_available": qdrant_status["available"],
        "qdrant_error": qdrant_status["last_error"],
        "redis_available": is_redis_available(),
        "startup_sync_ok": startup_sync_status["ok"],
        "startup_sync_error": startup_sync_status["error"],
    }


@app.get("/health/llm")
async def health_llm():
    result = llm_check_health()
    return result
