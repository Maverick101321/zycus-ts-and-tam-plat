import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "")
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

_raw_models = os.getenv(
    "OPENROUTER_MODELS",
    "nvidia/nemotron-3-ultra-550b-a55b:free,z-ai/glm-5.2:free",
)
OPENROUTER_MODELS: list[str] = [m.strip() for m in _raw_models.split(",") if m.strip()]

_raw_temperature = os.getenv("DEFAULT_TEMPERATURE", "0")
try:
    DEFAULT_TEMPERATURE: float = float(_raw_temperature)
except ValueError:
    DEFAULT_TEMPERATURE = 0.0

_raw_seed = os.getenv("DEFAULT_SEED", "42")
try:
    DEFAULT_SEED: int = int(_raw_seed)
except ValueError:
    DEFAULT_SEED = 42

