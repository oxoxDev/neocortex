"""Environment setup and configuration loading for notebooks."""

import json
import os
import sys
from pathlib import Path

# Resolve mk1/ from benchmarks/nb_helpers/config.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_REPO_ROOT = PROJECT_ROOT.parent

# API keys that the benchmark suite may need.
# Each entry: (env_var_name, display_label, required)
_API_KEYS = [
    ("OPENAI_API_KEY", "OpenAI API Key", True),
    ("NEOCORTEX_API_KEY", "Neocortex API Key", False),
]


def _prompt_api_keys():
    """Prompt for missing API keys interactively.

    Uses ``getpass`` so keys are not echoed in notebook output.
    Already-set env vars (from ``.env`` or the shell) are left untouched.
    """
    import getpass

    for env_var, label, required in _API_KEYS:
        existing = os.environ.get(env_var)
        if existing:
            masked = existing[:4] + "..." + existing[-4:] if len(existing) > 12 else "****"
            print(f"  {label} ({env_var}): {masked}")
            continue

        tag = "required" if required else "optional, Enter to skip"
        value = getpass.getpass(f"  Enter {label} ({tag}): ")
        if value.strip():
            os.environ[env_var] = value.strip()
            print(f"  {label}: set")
        elif required:
            print(f"  WARNING: {env_var} is not set — adapters that need it will fail.")
        else:
            print(f"  {label}: skipped")


def setup_environment():
    """Load .env, prompt for API keys, set up sys.path, and patch the event loop."""
    from dotenv import load_dotenv

    # Load .env from mk1/ directory (provides defaults)
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Prompt for any missing keys
    print("API keys:")
    _prompt_api_keys()
    print()

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
