"""mk1 adapter package.

Generic adapters live in ``helpers.adapters``.  This module registers the
mk1-specific neocortex adapters into the shared registry so that
``get_adapter("neocortex")`` works when running from mk1.
"""

import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path so ``helpers`` is importable.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(_REPO_ROOT))

from helpers.adapters import (  # noqa: E402, F401
  ADAPTER_NAMES,
  get_adapter,
  register_adapter,
)
from helpers.adapters._base import IndexResult, MethodAdapter, QueryResult  # noqa: E402, F401

# Register mk1-specific adapters as legacy (they expect list[str] / dict).
register_adapter("neocortex", ".neocortex", "NeocortexAdapter", package=__name__, legacy=True)
register_adapter("neocortex_v1", ".neocortex_v1", "NeocortexV1Adapter", package=__name__, legacy=True)

__all__ = [
  "ADAPTER_NAMES",
  "get_adapter",
  "register_adapter",
  "IndexResult",
  "MethodAdapter",
  "QueryResult",
]
