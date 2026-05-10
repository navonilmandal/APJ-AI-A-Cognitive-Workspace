from typing import List, Optional
from backend.schemas.memory import MemoryObject
from backend.memory.vector_store import VectorStore, get_vector_store

class MemoryService:
    """
    Cognitive Memory Management Service.
    Bridges between the API and Qdrant Vector Store.
    """
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def store_memory(self, memory: MemoryObject):
        self.vector_store.upsert_memories([memory])

    def store_memories(self, memories: List[MemoryObject]):
        self.vector_store.upsert_memories(memories)

    def retrieve_context(self, query: str, user_id: Optional[str] = None, limit: int = 5) -> List[MemoryObject]:
        results = self.vector_store.search(query, user_id=user_id, limit=limit)
        memories = []
        for res in results:
            # Reconstruct MemoryObject from payload
            payload = res['payload']
            memories.append(MemoryObject(**payload))
        return memories

# Singleton
_memory_service = None
def get_memory_service():
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService(get_vector_store())
    return _memory_service
