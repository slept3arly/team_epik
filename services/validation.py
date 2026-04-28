from __future__ import annotations

import re
from datetime import date, datetime
from typing import Iterable

CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
WHITESPACE_RE = re.compile(r"\s+")


def clean_text(value: object, *, max_length: int, allow_newlines: bool = False) -> str:
    text = "" if value is None else str(value)
    text = CONTROL_CHARS_RE.sub("", text).strip()
    if not allow_newlines:
        text = WHITESPACE_RE.sub(" ", text)
    if len(text) > max_length:
        raise ValueError(f"Text exceeds the {max_length}-character limit.")
    return text


def require_text(value: object, field_name: str, *, max_length: int, allow_newlines: bool = False) -> str:
    text = clean_text(value, max_length=max_length, allow_newlines=allow_newlines)
    if not text:
        raise ValueError(f"{field_name} is required.")
    return text


def clamp_int(value: object, field_name: str, *, minimum: int, maximum: int) -> int:
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be an integer.")
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{field_name} must be between {minimum} and {maximum}.")
    return parsed


def clamp_float(value: object, field_name: str, *, minimum: float, maximum: float) -> float:
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a number.")
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{field_name} must be between {minimum} and {maximum}.")
    return parsed


def parse_date(value: object, field_name: str) -> str:
    text = require_text(value, field_name, max_length=10)
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format.") from exc
    return parsed.isoformat()


def parse_choice(value: object, field_name: str, *, allowed: Iterable[str], max_length: int = 64) -> str:
    text = require_text(value, field_name, max_length=max_length)
    normalized = text.lower()
    allowed_set = {item.lower() for item in allowed}
    if normalized not in allowed_set:
        raise ValueError(f"{field_name} must be one of: {', '.join(sorted(allowed_set))}.")
    return normalized


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = "" if value is None else str(value).strip().lower()
    return text in {"1", "true", "yes", "on", "checked"}


def today_iso() -> str:
    return date.today().isoformat()

