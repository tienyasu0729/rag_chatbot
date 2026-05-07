"""
Text-to-SQL agent — sinh SQL từ câu hỏi, validate, execute.
"""

import json
import logging
from app.services.llm import chat_completion
from app.db import sqlserver

logger = logging.getLogger(__name__)

SQL_GEN_PROMPT = """Bạn là chuyên gia SQL Server. Viết câu truy vấn để trả lời câu hỏi bên dưới.

SCHEMA CÁC BẢNG ĐƯỢC PHÉP DÙNG:
- Vehicles (v):     id, title, price, year, mileage, fuel, transmission,
                    body_style, origin, description, status, is_deleted,
                    category_id, subcategory_id, branch_id
- Categories (c):   id, name          [JOIN: v.category_id = c.id]
- Subcategories (sc): id, name        [JOIN: v.subcategory_id = sc.id]
- Branches (b):     id, name, address [JOIN: v.branch_id = b.id]

QUY TẮC BẮT BUỘC:
1. Luôn có: WHERE v.status = 'Available' AND v.is_deleted = 0
2. Chỉ viết SELECT. TUYỆT ĐỐI không dùng: INSERT, UPDATE, DELETE, DROP, EXEC, ALTER, CREATE, TRUNCATE, MERGE
3. Không subquery lồng quá 2 cấp
4. Chỉ trả về SQL thuần, không markdown, không giải thích

Câu hỏi: "{query}" """

FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "EXEC",
    "ALTER", "CREATE", "TRUNCATE", "MERGE", "SP_", "XP_",
]


def validate_sql(sql: str) -> bool:
    """Kiểm tra SQL an toàn: chỉ SELECT, có WHERE Available, không có keyword nguy hiểm."""
    sql_upper = sql.upper().strip()

    # Loại bỏ markdown code fence nếu LLM trả về
    if sql_upper.startswith("```"):
        lines = sql.strip().split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        sql = "\n".join(lines)
        sql_upper = sql.upper().strip()

    if not sql_upper.startswith("SELECT"):
        logger.warning("SQL validation failed: not a SELECT")
        return False

    if "AVAILABLE" not in sql_upper:
        logger.warning("SQL validation failed: missing WHERE Available")
        return False

    for kw in FORBIDDEN_KEYWORDS:
        if kw in sql_upper:
            logger.warning("SQL validation failed: forbidden keyword '%s'", kw)
            return False

    return True


def clean_sql(sql: str) -> str:
    """Loại bỏ markdown code fence nếu có."""
    sql = sql.strip()
    if sql.startswith("```"):
        lines = sql.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        sql = "\n".join(lines).strip()
    return sql


def generate_and_execute_sql(query: str) -> dict:
    """
    Sinh SQL từ câu hỏi → validate → execute → trả kết quả.

    Returns:
        {
            "success": bool,
            "sql": str | None,
            "results": list[dict] | None,
            "error": str | None
        }
    """
    try:
        # 1. Gọi LLM sinh SQL
        prompt = SQL_GEN_PROMPT.format(query=query)
        raw_sql = chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=500,
        )

        sql = clean_sql(raw_sql)
        logger.info("Generated SQL: %s", sql)

        # 2. Validate
        if not validate_sql(sql):
            return {
                "success": False,
                "sql": sql,
                "results": None,
                "error": "SQL không hợp lệ",
            }

        # 3. Execute
        results = sqlserver.query(sql)
        logger.info("SQL executed: %d rows returned", len(results))

        return {
            "success": True,
            "sql": sql,
            "results": results,
            "error": None,
        }

    except Exception as e:
        logger.exception("SQL agent error")
        return {
            "success": False,
            "sql": None,
            "results": None,
            "error": str(e),
        }
