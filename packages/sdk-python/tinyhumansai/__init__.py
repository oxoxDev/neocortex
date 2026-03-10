"""TinyHumans Python SDK."""

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
]

# Conditional integration re-exports
try:
    from .integrations import TinyHumanStore  # noqa: F401

    __all__.append("TinyHumanStore")
except ImportError:
    pass

try:
    from .integrations import TinyHumanChatMessageHistory  # noqa: F401

    __all__.append("TinyHumanChatMessageHistory")
except ImportError:
    pass
