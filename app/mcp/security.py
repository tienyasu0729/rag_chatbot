"""
Validation và sanitize cho MCP tool params.
"""

from __future__ import annotations

import re

from app.db import sqlserver

_SAFE_STRING = re.compile(r"^[\w\s\-\./]+$", re.UNICODE)
_MAX_STRING_LENGTH = 100
_DYNAMIC_ENUM_QUERIES = {
    "fuel_type": "SELECT name FROM VehicleFuelTypes WHERE status = 'active' ORDER BY name",
    "transmission": "SELECT name FROM VehicleTransmissions WHERE status = 'active' ORDER BY name",
}
_dynamic_enum_cache: dict[str, set[str]] = {}


class InvalidParamsError(ValueError):
    """Tham số tool không hợp lệ."""


def sanitize_string(value: str) -> str:
    cleaned = " ".join(value.strip().split())
    if len(cleaned) > _MAX_STRING_LENGTH:
        raise InvalidParamsError("Chuỗi vượt quá độ dài cho phép")
    if not _SAFE_STRING.match(cleaned):
        raise InvalidParamsError("Chuỗi chứa ký tự không hợp lệ")
    return cleaned


def sanitize_string_params(params: dict) -> dict:
    sanitized: dict = {}
    for key, value in params.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_string(item) if isinstance(item, str) else item for item in value]
        else:
            sanitized[key] = value
    return sanitized


def normalize_enum_value(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _get_dynamic_enum(field_name: str) -> set[str]:
    cached = _dynamic_enum_cache.get(field_name)
    if cached is not None:
        return cached

    sql = _DYNAMIC_ENUM_QUERIES[field_name]
    rows = sqlserver.query_readonly(sql)
    values = {normalize_enum_value(row["name"]) for row in rows if row.get("name")}
    _dynamic_enum_cache[field_name] = values
    return values


def validate_enum_params(params: dict, schema: dict) -> dict:
    properties = schema.get("properties", {})
    normalized = dict(params)

    for field_name, field_schema in properties.items():
        if field_name not in normalized or normalized[field_name] is None:
            continue

        value = normalized[field_name]
        enum_values = field_schema.get("enum")
        dynamic_enum = field_schema.get("dynamic_enum")

        if enum_values and isinstance(value, str):
            normalized_value = normalize_enum_value(value)
            allowed = {normalize_enum_value(item) for item in enum_values}
            if normalized_value not in allowed:
                raise InvalidParamsError(f"Giá trị '{field_name}' không hợp lệ")
            normalized[field_name] = normalized_value
        elif dynamic_enum and isinstance(value, str):
            normalized_value = normalize_enum_value(value)
            allowed = _get_dynamic_enum(dynamic_enum)
            if normalized_value not in allowed:
                raise InvalidParamsError(f"Giá trị '{field_name}' không có trong danh mục hỗ trợ")
            normalized[field_name] = normalized_value

    return normalized


def validate_params_shape(params: dict, schema: dict) -> dict:
    if not isinstance(params, dict):
        raise InvalidParamsError("Params phải là object")

    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    additional = schema.get("additionalProperties", False)

    for req_key in required:
        if req_key not in params:
            raise InvalidParamsError(f"Thiếu tham số bắt buộc: {req_key}")

    if not additional:
        for key in params:
            if key not in properties:
                raise InvalidParamsError(f"Tham số không được phép: {key}")

    validated: dict = {}
    for key, value in params.items():
        field_schema = properties.get(key)
        if field_schema is None:
            continue
        validated[key] = _validate_value(key, value, field_schema)
    return validated


def _validate_value(field_name: str, value, field_schema: dict):
    field_type = field_schema.get("type")

    if value is None:
        return None
    if field_type == "string":
        if not isinstance(value, str):
            raise InvalidParamsError(f"'{field_name}' phải là string")
        return value
    if field_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidParamsError(f"'{field_name}' phải là integer")
        return value
    if field_type == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise InvalidParamsError(f"'{field_name}' phải là number")
        return float(value)
    if field_type == "array":
        if not isinstance(value, list):
            raise InvalidParamsError(f"'{field_name}' phải là array")
        item_schema = field_schema.get("items", {})
        return [_validate_value(field_name, item, item_schema) for item in value]
    if field_type == "object":
        if not isinstance(value, dict):
            raise InvalidParamsError(f"'{field_name}' phải là object")
        nested_props = field_schema.get("properties", {})
        return {
            nested_key: _validate_value(nested_key, nested_value, nested_props[nested_key])
            for nested_key, nested_value in value.items()
            if nested_key in nested_props
        }
    raise InvalidParamsError(f"Kiểu dữ liệu của '{field_name}' chưa được hỗ trợ")
