"""Environment setup and configuration loading for notebooks."""

import json
import sys
from pathlib import Path

# Resolve mk1/ from benchmarks/nb_helpers/config.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_REPO_ROOT = PROJECT_ROOT.parent


def setup_environment():
    """Load .env, add project root and repo root to sys.path."""
    from dotenv import load_dotenv

    # Load .env from mk1/ directory
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Ensure mk1/ is importable (for `from adapters import ...`)
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    # Ensure repo root is importable (for `from helpers import ...`)
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))

    # Apply nest_asyncio for Jupyter event loop compatibility
    import nest_asyncio

    nest_asyncio.apply()


def load_config(overrides: dict | None = None) -> dict:
    """Load config.json from mk1/ and merge optional overrides.

    Args:
        overrides: Dict of keys to override in the loaded config.

    Returns:
        Merged config dict.
    """
    config_path = PROJECT_ROOT / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
    else:
        config = {}

    if overrides:
        config.update(overrides)

    return config
