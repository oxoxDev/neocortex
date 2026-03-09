"""Re-export base classes from helpers for backward compatibility.

Legacy adapters (e.g. neocortex .pyc files) import from ``._base``.
This shim ensures they continue to work after the move to ``helpers/``.
"""

import sys
from pathlib import Path

# Ensure repo root is on path so helpers and neocortex are importable
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(_REPO_ROOT))

from helpers.adapters._base import (  # noqa: F401, E402
  SHERLOCK_DOMAIN,
  SHERLOCK_ENTITY_TYPES,
  SHERLOCK_QUERIES,
  MethodAdapter,
  _get_cost_tracker,
)
from helpers.types import (  # noqa: F401, E402
  BenchmarkConfig,
  Chunk,
  IndexResult,
  QueryResult,
)
