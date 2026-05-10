import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Config:
    """Centralized configuration for the Cognitive AI Assistant."""
    
    # Project Paths
    PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", "E:/ai_ml_intern"))
    BACKEND_DIR = PROJECT_ROOT / "backend"
    DATA_DIR = PROJECT_ROOT / "data"
    CACHE_DIR = PROJECT_ROOT / "cache"
    HF_HOME = PROJECT_ROOT / "hf_cache"
    MODELS_DIR = PROJECT_ROOT / "models"
    QDRANT_DATA = PROJECT_ROOT / "qdrant_data"
    
    # Ensure critical directories exist
    for path in [CACHE_DIR, HF_HOME, MODELS_DIR, QDRANT_DATA]:
        path.mkdir(parents=True, exist_ok=True)
        
    # Qdrant Settings
    QDRANT_PATH = QDRANT_DATA / "local_storage"
    DEFAULT_COLLECTION = "conversational_memory"
    
    # Local LLM
    LLM_MODEL_PATH: Path = MODELS_DIR / "qwen2.5-3b-instruct-q4_k_m.gguf"
    
    # Cloud Providers
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    
    # Routing Settings
    DEFAULT_ROUTING_MODE: str = os.getenv("DEFAULT_ROUTING_MODE", "hybrid") # local, cloud, hybrid
    COMPLEXITY_THRESHOLD: float = float(os.getenv("COMPLEXITY_THRESHOLD", 0.6))

    # Model Settings
    GGUF_MODEL_PATH = Path(os.getenv("GGUF_MODEL_PATH", MODELS_DIR / "qwen2.5-3b-instruct-q4_k_m.gguf"))
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # API Settings
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

settings = Config()
