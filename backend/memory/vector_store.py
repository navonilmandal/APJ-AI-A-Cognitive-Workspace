from qdrant_client import models
from backend.memory.qdrant_client import get_qdrant_client
from typing import List, Dict, Any, Optional
import uuid
from backend.core.config import settings
from backend.models.embedding_service import get_embedding_service
from backend.schemas.memory import MemoryObject
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

class VectorStore:
    """
    Persistent Cognitive Memory Store using Qdrant.
    Handles vector indexing, metadata payloads, and semantic search.
    """
    def __init__(self, collection_name: str = None):
        self.collection_name = collection_name or settings.DEFAULT_COLLECTION
        self.client = get_qdrant_client()
        self.embedding_service = get_embedding_service()
        
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensures the Qdrant collection exists with the correct dimensions."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                dimension = self.embedding_service.get_dimension()
                logger.info(f"Creating Qdrant collection: {self.collection_name} (dim={dimension})")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=dimension, 
                        distance=models.Distance.COSINE
                    )
                )
        except Exception as e:
            logger.error(f"Error checking/creating Qdrant collection: {e}")

    def upsert_memories(self, memories: List[MemoryObject]):
        """Embeds and inserts MemoryObjects into Qdrant."""
        if not memories:
            return

        points = []
        for memory in memories:
            vector = self.embedding_service.embed_text(memory.message)
            point_id = str(uuid.uuid4())
            
            points.append(models.PointStruct(
                id=point_id,
                vector=vector,
                payload=memory.model_dump()
            ))

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info(f"Inserted {len(memories)} vectors into Qdrant collection '{self.collection_name}'.")

    def search(self, query: str, user_id: Optional[str] = None, limit: int = 5, score_threshold: float = 0.35) -> List[Dict[str, Any]]:
        """
        Performs semantic search with optional user isolation filtering.
        """
        query_vector = self.embedding_service.embed_text(query)
        
        query_filter = None
        if user_id:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id)
                    )
                ]
            )

        # Use query_points (Modern Qdrant 1.11+ API)
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True
        ).points
        
        results = []
        for hit in search_result:
            results.append({
                "payload": hit.payload,
                "score": hit.score,
                "id": hit.id
            })
        
        return results

    def delete_collection(self):
        """Deletes the entire collection."""
        self.client.delete_collection(self.collection_name)
        logger.info(f"Deleted collection '{self.collection_name}'.")

# Singleton Accessor
_vector_store = None

def get_vector_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
