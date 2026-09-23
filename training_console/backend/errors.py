"""Unified API errors independent of FastAPI's exception classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConsoleError(Exception):
    code: str
    message: str
    category: str
    status_code: int = 400
    details: dict[str, Any] = field(default_factory=dict)

    def body(self) -> dict[str, Any]:
        return {"error": {"code": self.code, "message": self.message, "category": self.category, "details": self.details}}


def validation(message: str, details: dict[str, Any] | None = None) -> ConsoleError:
    return ConsoleError("VALIDATION_ERROR", message, "validation", 422, details or {})


def not_found(message: str, details: dict[str, Any] | None = None) -> ConsoleError:
    return ConsoleError("RESOURCE_NOT_FOUND", message, "not_found", 404, details or {})


def conflict(message: str, details: dict[str, Any] | None = None) -> ConsoleError:
    return ConsoleError("RESOURCE_CONFLICT", message, "conflict", 409, details or {})

