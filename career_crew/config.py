import os
from crewai import LLM
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # "ollama", "gemini", "openai", "anthropic"

# Ollama Settings
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Gemini Settings
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash-exp",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2-flash",
    "gemini-2-flash-lite",
    "gemini-3-flash",
    "gemini-3.1-pro",
    "gemini-3.1-flash-lite",
    "gemma-3-1b",
    "gemma-3-4b",
    "gemma-3-12b",
    "gemma-3-27b"
]

# OpenAI Settings
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "o1-mini",
    "o3-mini",
]

# Anthropic Settings
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODELS = [
    "claude-opus-4-8",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
]

# Jina Reader API Settings
JINA_API_KEY = os.getenv("JINA_API_KEY", "")

# Directory Settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
INPUTS_DIR = os.path.join(BASE_DIR, "inputs")

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(INPUTS_DIR, exist_ok=True)

# App Settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))


def get_llm(provider: str = None, model: str = None, api_key: str = None, base_url: str = None):
    """Returns correct LLM object based on provider and model parameters."""
    p = (provider or LLM_PROVIDER).lower()

    if p == "gemini":
        m = model or GEMINI_MODEL
        key = api_key or GEMINI_API_KEY
        return LLM(model=f"gemini/{m}", api_key=key)

    if p == "openai":
        m = model or OPENAI_MODEL
        key = api_key or OPENAI_API_KEY
        return LLM(model=m, api_key=key)

    if p == "anthropic":
        m = model or ANTHROPIC_MODEL
        key = api_key or ANTHROPIC_API_KEY
        return LLM(model=f"anthropic/{m}", api_key=key)

    # Default: Ollama
    m = model or OLLAMA_MODEL
    url = base_url or OLLAMA_BASE_URL
    return LLM(model=f"ollama/{m}", base_url=url)


def get_active_model_name(provider: str = None, model: str = None) -> str:
    """Returns the display name of the active model."""
    p = (provider or LLM_PROVIDER).lower()
    if p == "gemini":
        return model or GEMINI_MODEL
    if p == "openai":
        return model or OPENAI_MODEL
    if p == "anthropic":
        return model or ANTHROPIC_MODEL
    return model or OLLAMA_MODEL
