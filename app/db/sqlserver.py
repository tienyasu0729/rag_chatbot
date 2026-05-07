"""
SQL Server connection pool và helper functions.
Sử dụng pyodbc với connection pooling mặc định.
"""

import logging
import pyodbc
from app.config import get_settings

logger = logging.getLogger(__name__)

# Bật connection pooling của pyodbc
pyodbc.pooling = True

_connection_string: str | None = None
_readonly_connection_string: str | None = None


def _get_conn_str() -> str:
    global _connection_string
    if _connection_string is None:
        _connection_string = get_settings().sqlserver_connection_string
    return _connection_string


def _get_readonly_conn_str() -> str:
    global _readonly_connection_string
    if _readonly_connection_string is None:
        _readonly_connection_string = get_settings().sqlserver_readonly_connection_string
    return _readonly_connection_string


def get_connection() -> pyodbc.Connection:
    """Lấy connection từ pool. Caller phải tự close."""
    return pyodbc.connect(_get_conn_str(), autocommit=False)


def get_readonly_connection() -> pyodbc.Connection:
    """Lấy read-only connection từ pool. Caller phải tự close."""
    return pyodbc.connect(_get_readonly_conn_str(), autocommit=False)


def query(sql: str, params: dict | None = None, timeout: int | None = None, commit: bool = False) -> list[dict]:
    """
    Thực thi SELECT query, trả về list[dict].
    Params dùng dạng named: @param_name trong SQL.
    Set commit=True cho INSERT/UPDATE có OUTPUT clause.
    """
    settings = get_settings()
    _timeout = timeout or settings.SQL_QUERY_TIMEOUT

    conn = get_connection()
    try:
        conn.timeout = _timeout
        cursor = conn.cursor()

        # Chuyển named params (@name) sang positional (?)
        if params:
            sql_exec, values = _convert_named_params(sql, params)
            cursor.execute(sql_exec, values)
        else:
            cursor.execute(sql)

        columns = [col[0] for col in cursor.description] if cursor.description else []
        rows = cursor.fetchall()

        if commit:
            conn.commit()

        return [dict(zip(columns, row)) for row in rows]
    except Exception:
        if commit:
            conn.rollback()
        logger.exception("SQL query error")
        raise
    finally:
        conn.close()


def query_readonly(sql: str, params: dict | None = None, timeout: int | None = None) -> list[dict]:
    """
    Thực thi SELECT query bằng read-only credentials, trả về list[dict].
    Params dùng dạng named: @param_name trong SQL.
    """
    settings = get_settings()
    _timeout = timeout or settings.SQL_QUERY_TIMEOUT

    conn = get_readonly_connection()
    try:
        conn.timeout = _timeout
        cursor = conn.cursor()

        if params:
            sql_exec, values = _convert_named_params(sql, params)
            cursor.execute(sql_exec, values)
        else:
            cursor.execute(sql)

        columns = [col[0] for col in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    except Exception:
        logger.exception("SQL query_readonly error")
        raise
    finally:
        conn.close()


def execute(sql: str, params: dict | None = None, timeout: int | None = None) -> int:
    """
    Thực thi INSERT/UPDATE/DELETE, trả về số dòng affected.
    """
    settings = get_settings()
    _timeout = timeout or settings.SQL_QUERY_TIMEOUT

    conn = get_connection()
    try:
        conn.timeout = _timeout
        cursor = conn.cursor()

        if params:
            sql_exec, values = _convert_named_params(sql, params)
            cursor.execute(sql_exec, values)
        else:
            cursor.execute(sql)

        rowcount = cursor.rowcount
        conn.commit()
        return rowcount
    except Exception:
        conn.rollback()
        logger.exception("SQL execute error")
        raise
    finally:
        conn.close()


def query_one(sql: str, params: dict | None = None, timeout: int | None = None) -> dict | None:
    """Trả về 1 row hoặc None."""
    rows = query(sql, params, timeout)
    return rows[0] if rows else None


def query_one_readonly(sql: str, params: dict | None = None, timeout: int | None = None) -> dict | None:
    """Trả về 1 row hoặc None bằng read-only credentials."""
    rows = query_readonly(sql, params, timeout)
    return rows[0] if rows else None


def query_positional(sql: str, params: list | None = None, timeout: int | None = None) -> list[dict]:
    """
    Thực thi SELECT với positional params (?).
    Dùng cho trường hợp cần IN (?, ?, ...) mà named params không hỗ trợ.
    """
    settings = get_settings()
    _timeout = timeout or settings.SQL_QUERY_TIMEOUT

    conn = get_connection()
    try:
        conn.timeout = _timeout
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        columns = [col[0] for col in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    except Exception:
        logger.exception("SQL query_positional error")
        raise
    finally:
        conn.close()


def query_positional_readonly(sql: str, params: list | None = None, timeout: int | None = None) -> list[dict]:
    """
    Thực thi SELECT với positional params (?) bằng read-only credentials.
    """
    settings = get_settings()
    _timeout = timeout or settings.SQL_QUERY_TIMEOUT

    conn = get_readonly_connection()
    try:
        conn.timeout = _timeout
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        columns = [col[0] for col in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    except Exception:
        logger.exception("SQL query_positional_readonly error")
        raise
    finally:
        conn.close()


def _convert_named_params(sql: str, params: dict) -> tuple[str, list]:
    """
    Chuyển đổi named params kiểu @param_name sang ? placeholder cho pyodbc.
    Ví dụ: "WHERE id = @id" + {"id": 1} → "WHERE id = ?" + [1]
    """
    import re

    values = []
    used_params = []

    # Tìm tất cả @param_name trong SQL
    pattern = re.compile(r'@(\w+)')
    matches = pattern.findall(sql)

    for match in matches:
        if match in params:
            used_params.append(match)

    # Thay thế @param_name bằng ? theo thứ tự xuất hiện
    sql_exec = sql
    values = []
    for match in matches:
        if match in params:
            sql_exec = sql_exec.replace(f"@{match}", "?", 1)
            values.append(params[match])

    return sql_exec, values
