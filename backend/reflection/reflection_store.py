from datetime import datetime
from typing import List, Dict, Any, Optional
from qdrant_client import models
from backend.memory.qdrant_client import get_qdrant_client
from backend.core.config import settings
from backend.models.embedding_service import get_embedding_service
from backend.reflection.schemas import ReflectionObject
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

class ReflectionStore:
    """
    Dedicated store for high-level cognitive reflections and insights.
    Uses a separate Qdrant collection 'user_reflections'.
    """
    def __init__(self):
        self.collection_name = "user_reflections"
        self.client = get_qdrant_client()
        self.embedding_service = get_embedding_service()
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                dimension = self.embedding_service.get_dimension()
                logger.info(f"Creating Reflection collection: {self.collection_name} (dim={dimension})")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE)
                )
        except Exception as e:
            logger.error(f"Error initializing ReflectionStore: {e}")

    def save_reflection(self, reflection: ReflectionObject):
        """Saves or updates a reflection in Qdrant."""
        # Calculate strength based on confidence
        if reflection.confidence < 0.6:
            reflection.strength = "weak"
        elif reflection.confidence < 0.8:
            reflection.strength = "medium"
        else:
            reflection.strength = "strong"
            
        reflection.updated_at = datetime.now()
        reflection.evidence_count = len(reflection.evidence)
        
        vector = self.embedding_service.embed_text(reflection.insight)
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[models.PointStruct(
                id=reflection.reflection_id,
                vector=vector,
                payload=reflection.model_dump(mode='json')
            )]
        )
        logger.info(f"Persisted [{reflection.strength}] {reflection.type}: {reflection.insight[:50]}... (Conf: {reflection.confidence:.2f})")

    def get_reflections(self, 
                        user_id: str = "default_user",
                        reflection_type: Optional[str] = None, 
                        min_strength: Optional[str] = None,
                        limit: int = 20) -> List[ReflectionObject]:
        """Retrieves reflections with optional type and strength filtering."""
        must_filters = [
            models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
        ]
        if reflection_type:
            must_filters.append(models.FieldCondition(key="type", match=models.MatchValue(value=reflection_type)))
        
        if min_strength:
            # Simple strength hierarchy
            strengths = ["weak", "medium", "strong"]
            target_strengths = strengths[strengths.index(min_strength):]
            must_filters.append(models.FieldCondition(key="strength", match=models.MatchAny(any=target_strengths)))

        query_filter = models.Filter(must=must_filters) if must_filters else None

        hits = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=query_filter,
            limit=limit,
            with_payload=True
        )[0]
        
        return [ReflectionObject(**hit.payload) for hit in hits]

    def search_reflections(self, query: str, user_id: str = "default_user", limit: int = 5) -> List[ReflectionObject]:
        """Semantically searches through existing reflections for a specific user."""
        vector = self.embedding_service.embed_text(query)
        
        query_filter = models.Filter(
            must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
        )
        
        hits = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        ).points
        
        return [ReflectionObject(**hit.payload) for hit in hits]

# Singleton
_reflection_store = None
def get_reflection_store():
    global _reflection_store
    if _reflection_store is None:
        _reflection_store = ReflectionStore()
    return _reflection_store
