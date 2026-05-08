"""
Intent Classifier — phân loại ý định người dùng.
RAG / SQL / RECOMMEND / CLARIFY / OTHER.
Rule-based trước, fallback LLM khi không chắc.
"""

import json
import re
import logging
from app.services.llm import chat_completion

logger = logging.getLogger(__name__)

_SQL_KEYWORDS = re.compile(
    r"bao nhiêu|mấy (chiếc|xe|cái)|đếm|tổng\b|trung bình|cao nhất|thấp nhất"
    r"|nhiều nhất|ít nhất|thống kê|tổng cộng|count|sum|avg|min|max"
    r"|còn hàng|hết hàng|hết chưa|đang còn|còn (bao|mấy|không)"
    r"|tất cả xe|liệt kê hết|danh sách.{0,10}(tất cả|toàn bộ|đầy đủ)"
    r"|số lượng|giá (rẻ|đắt|thấp|cao) nhất",
    re.IGNORECASE,
)
_OTHER_KEYWORDS = re.compile(
    r"^(xin chào|hello|hi|hey|bạn tên gì|bạn là ai|cảm ơn|tạm biệt|bye)\s*[?!.]*$",
    re.IGNORECASE,
)
_RECOMMEND_KEYWORDS = re.compile(
    r"tư vấn|gợi ý|giúp.{0,10}chọn xe|nên mua|xe nào.{0,15}(phù hợp|tốt|hợp)"
    r"|muốn mua xe|tìm xe|chọn xe|recommend"
    r"|có xe (nào|không).{0,30}(phù hợp|dưới|trên|tầm|khoảng)"
    r"|xe.{0,10}(gia đình|cá nhân|đi làm|dưới \d|tầm \d)"
    r"|\d\s*(chỗ|người).{0,20}(dưới|khoảng|tầm)"
    r"|(dưới|khoảng|tầm).{0,15}(tỷ|triệu).{0,20}(xe|mua|chọn)",
    re.IGNORECASE,
)

_VALID_INTENTS = ("RAG", "SQL", "OTHER", "RECOMMEND", "CLARIFY")

INTENT_PROMPT = """Bạn là bộ phân loại ý định cho chatbot tư vấn xe hơi.
Phân loại câu hỏi sau vào đúng 1 trong 5 nhóm:

- "RECOMMEND": User muốn tư vấn/gợi ý xe theo nhu cầu, không hỏi xe cụ thể
  Ví dụ: "tư vấn xe cho tôi", "xe nào phù hợp gia đình", "giúp em chọn xe"

- "CLARIFY": User đang trả lời câu hỏi của bot về nhu cầu/ngân sách/mục đích
  Ví dụ: "khoảng 400 triệu", "đi trong thành phố là chính", "cần 7 chỗ"

- "RAG": Hỏi thông tin, đặc điểm, so sánh xe cụ thể (có tên xe hoặc loại xe rõ ràng)
  Ví dụ: "Toyota Vios có màu gì?", "So sánh Vios và City", "xe Honda có gì đặc biệt?"

- "SQL": Hỏi số lượng, thống kê, đếm, tính toán, liệt kê tất cả, hoặc kiểm tra còn hàng/hết hàng
  Ví dụ: "Còn bao nhiêu xe Toyota?", "Giá rẻ nhất là bao nhiêu?", "Xe Honda còn hàng không?", "Tất cả xe đang bán", "Liệt kê hết xe Ford"

- "OTHER": Chào hỏi, hỏi ngoài phạm vi xe
  Ví dụ: "Bạn tên gì?", "Hôm nay thứ mấy?"

Lịch sử hội thoại gần nhất:
{history}

Câu hỏi hiện tại: "{query}"

Chỉ trả về JSON, không thêm bất kỳ ký tự nào khác:
{{"intent": "RECOMMEND"}} hoặc {{"intent": "CLARIFY"}} hoặc {{"intent": "RAG"}} hoặc {{"intent": "SQL"}} hoặc {{"intent": "OTHER"}}"""


def _is_short_answer(query: str) -> bool:
    """Detect short replies typical of CLARIFY (budget, purpose answers)."""
    stripped = query.strip().rstrip(".,!?")
    words = stripped.split()
    return len(words) <= 8


def _last_bot_asked_question(history: list[dict]) -> bool:
    """Check if the last bot message ended with a question."""
    if not history:
        return False
    for msg in reversed(history):
        if msg["role"] == "ai":
            content = msg["content"].strip()
            return content.endswith("?") or "ạ?" in content or "không?" in content
    return False


def classify_intent(query: str, history: list[dict]) -> str:
    """
    Phân loại intent.
    Trả về: "RAG", "SQL", "RECOMMEND", "CLARIFY", hoặc "OTHER".
    """
    # Rule-based fast path
    if _OTHER_KEYWORDS.match(query.strip()):
        logger.info("Intent classified (rule): OTHER (query: %s)", query[:80])
        return "OTHER"
    if _SQL_KEYWORDS.search(query):
        logger.info("Intent classified (rule): SQL (query: %s)", query[:80])
        return "SQL"
    if _RECOMMEND_KEYWORDS.search(query):
        logger.info("Intent classified (rule): RECOMMEND (query: %s)", query[:80])
        return "RECOMMEND"
    if _is_short_answer(query) and _last_bot_asked_question(history):
        logger.info("Intent classified (rule): CLARIFY (query: %s)", query[:80])
        return "CLARIFY"

    # Format lịch sử
    if history:
        lines = []
        for msg in history:
            role = "Khách" if msg["role"] == "user" else "Tư vấn viên"
            lines.append(f"{role}: {msg['content']}")
        history_text = "\n".join(lines)
    else:
        history_text = "(Chưa có lịch sử)"

    prompt = INTENT_PROMPT.format(history=history_text, query=query)

    try:
        response = chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=50,
        )

        data = json.loads(response.strip())
        intent = data.get("intent", "RAG").upper()

        if intent in _VALID_INTENTS:
            logger.info("Intent classified: %s (query: %s)", intent, query[:80])
            return intent

        logger.warning("Unknown intent '%s', fallback to RAG", intent)
        return "RAG"

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Intent parse error: %s — fallback to RAG", e)
        return "RAG"
    except Exception:
        logger.exception("Intent classifier failed — fallback to RAG")
        return "RAG"
