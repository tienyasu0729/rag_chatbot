"""
LLM wrapper cho OpenAI-compatible gateway qua LLM_BASE_URL + API_KEY.
"""

import json
import logging
import re

from app.config import get_settings

logger = logging.getLogger(__name__)

_DEFAULT_GATEWAY_URL = "http://localhost:11434/v1"

_model: str | None = None
_openai_client = None


def _get_model(override: str | None = None) -> str:
    if override:
        return override
    if _model:
        return _model
    settings = get_settings()
    model = settings.LLM_MODEL.strip()
    if not model:
        raise RuntimeError("Thieu LLM_MODEL trong .env")
    return model


def _get_base_url() -> str:
    raw = get_settings().LLM_BASE_URL.strip()
    if raw and raw.startswith(("http://", "https://")):
        return raw
    return _DEFAULT_GATEWAY_URL


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI

        settings = get_settings()
        api_key = settings.API_KEY.strip()
        if not api_key:
            raise RuntimeError("Thieu API_KEY cho LLM gateway")

        _openai_client = OpenAI(
            base_url=_get_base_url(),
            api_key=api_key,
        )
    return _openai_client


_THINK_CLOSED_RE = re.compile(r"<think>[\s\S]*?</think>\s*", re.IGNORECASE)
_THINK_UNCLOSED_RE = re.compile(r"<think>[\s\S]*$", re.IGNORECASE)


def _strip_thinking(text: str) -> str:
    text = _THINK_CLOSED_RE.sub("", text)
    text = _THINK_UNCLOSED_RE.sub("", text)
    return text.strip()


def chat_completion(
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 1024,
    model: str | None = None,
) -> str:
    try:
        raw = _call_openai_gateway(messages, temperature, max_tokens, model)
        return _strip_thinking(raw)
    except Exception:
        logger.exception("LLM API call failed (model=%s)", _get_model(model))
        raise


def json_completion(
    messages: list[dict],
    schema_hint: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    model: str | None = None,
) -> dict:
    json_messages = list(messages)
    if schema_hint:
        json_messages.append(
            {
                "role": "user",
                "content": (
                    "Chi tra ve JSON object hop le, khong markdown, khong giai thich. "
                    f"Schema goi y: {schema_hint}"
                ),
            }
        )

    raw = chat_completion(
        messages=json_messages,
        temperature=temperature,
        max_tokens=max_tokens,
        model=model,
    )
    json_text = _extract_json_object(raw)
    payload = json.loads(json_text)
    if not isinstance(payload, dict):
        raise ValueError("LLM khong tra ve JSON object")
    return payload


def _call_openai_gateway(
    messages: list[dict], temperature: float, max_tokens: int, model: str | None
) -> str:
    client = _get_openai_client()
    _m = _get_model(model)

    response = client.chat.completions.create(
        model=_m,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content
    return (content or "").strip()


def _extract_json_object(text: str) -> str:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    if start < 0:
        raise ValueError("Khong tim thay JSON object trong response")

    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]

    raise ValueError("JSON object khong day du")


def check_health() -> dict:
    model = _get_model()
    base_url = _get_base_url()
    try:
        result = chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            temperature=0,
            max_tokens=5,
        )
        return {
            "status": "ok",
            "provider": "gateway",
            "model": model,
            "base_url": base_url,
            "message": f"API hoat dong binh thuong (response: {result[:30]})",
        }
    except Exception as e:
        error_str = str(e)
        if "429" in error_str:
            status = "quota_exhausted"
            message = "API key het quota hoac bi rate limit."
        elif "401" in error_str or "invalid" in error_str.lower():
            status = "invalid_key"
            message = "API key khong hop le."
        elif "Connection" in error_str or "refused" in error_str.lower():
            status = "connection_error"
            message = "Khong the ket noi toi LLM_BASE_URL."
        else:
            status = "error"
            message = f"Loi khong xac dinh: {error_str[:200]}"

        return {
            "status": status,
            "provider": "gateway",
            "model": model,
            "base_url": base_url,
            "message": message,
        }
