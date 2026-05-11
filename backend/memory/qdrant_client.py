from qdrant_client import QdrantClient
from backend.core.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

# Shared Qdrant Client Instance
_client = None

def get_qdrant_client():
    """
    Returns a shared singleton instance of the Qdrant client.
    Prioritizes URL/Host connections for Docker/Production environments.
    """
    global _client
    if _client is None:
        if settings.QDRANT_URL:
            logger.info(f"Initializing Qdrant Client at {settings.QDRANT_URL}")
            _client = QdrantClient(url=settings.QDRANT_URL)
        elif os.getenv("ENV") == "production" or os.getenv("QDRANT_HOST"):
            logger.info(f"Initializing Qdrant Client at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
            _client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        else:
            logger.info(f"Initializing Local Qdrant Client at {settings.QDRANT_PATH}")
            _client = QdrantClient(path=str(settings.QDRANT_PATH))
    return _client
