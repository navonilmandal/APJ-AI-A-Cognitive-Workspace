from qdrant_client import QdrantClient
from backend.core.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

# Shared Qdrant Client Instance
_client = None

def get_qdrant_client():
    """
    Returns a shared singleton instance of the Qdrant client.
    Ensures no 'Folder already accessed' errors occur within the same process.
    """
    global _client
    if _client is None:
        logger.info(f"Initializing Shared Qdrant Client at {settings.QDRANT_PATH}")
        _client = QdrantClient(path=str(settings.QDRANT_PATH))
    return _client
