"""TinyHumans Python SDK."""

from __future__ import annotations

import logging
import os

from .client import TinyHumanMemoryClient
from .llm import SUPPORTED_LLM_PROVIDERS
from .types import (
    TinyHumanError,
    DeleteMemoryResponse,
    GetContextResponse,
    IngestMemoryResponse,
    LLMQueryResponse,
    MemoryItem,
    ReadMemoryItem,
)

logger = logging.getLogger("tinyhumansai")

_level = os.environ.get("TINYHUMANSAI_LOG_LEVEL")
if _level:
    # Optional, env-driven log level for easier debugging in apps and notebooks.
    logger.setLevel(_level.upper())

__all__ = [
    "TinyHumanMemoryClient",
    "TinyHumanError",
    "DeleteMemoryResponse",
    "IngestMemoryResponse",
    "LLMQueryResponse",
    "MemoryItem",
    "GetContextResponse",
    "ReadMemoryItem",
    "SUPPORTED_LLM_PROVIDERS",
    "logger",
]