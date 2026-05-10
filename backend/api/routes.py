from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from backend.memory.vector_store import get_vector_store
from backend.memory.qdrant_client import get_qdrant_client
from backend.reflection.reflection_engine import get_reflection_engine
from backend.reflection.reflection_store import get_reflection_store
from backend.reflection.schemas import ReflectionObject, CognitiveProfile
from backend.schemas.memory import MemoryObject
from backend.utils.logger import setup_logger

from backend.router.response_pipeline import get_response_pipeline
from backend.memory.service import get_memory_service
from backend.schemas.response import HybridResponse

logger = setup_logger(__name__)
router = APIRouter()

from backend.schemas.chat import ChatRequest

@router.post("/chat", response_model=HybridResponse)
async def chat_query(request: ChatRequest):
    try:
        memory_service = get_memory_service()
        reflection_engine = get_reflection_engine()
        pipeline = get_response_pipeline(memory_service, reflection_engine)
        
        response = await pipeline.execute(request.query, user_id=request.user_id)
        return response
    except Exception as e:
        logger.error(f"Chat pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "cognitive-assistant-v2"}

@router.post("/memory/ingest")
async def ingest_memory(memories: List[MemoryObject]):
    try:
        store = get_vector_store()
        store.upsert_memories(memories)
        return {"status": "success", "count": len(memories)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.get("/memory/search")
async def search_memory(query: str, user_id: str = "default_user", limit: int = 5):
    try:
        store = get_vector_store()
        return store.search(query, user_id=user_id, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/reflection/generate", response_model=List[ReflectionObject])
async def generate_reflections(user_id: str = "default_user", query: Optional[str] = None):
    try:
        engine = get_reflection_engine()
        return engine.run_reflection_cycle(user_id=user_id, query=query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reflection cycle failed: {str(e)}")

@router.get("/reflection/list", response_model=List[ReflectionObject])
async def list_reflections(user_id: str = "default_user",
                           type: Optional[str] = None, 
                           min_strength: Optional[str] = Query(None, pattern="^(weak|medium|strong)$"),
                           limit: int = 20):
    try:
        store = get_reflection_store()
        return store.get_reflections(user_id=user_id, reflection_type=type, min_strength=min_strength, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch reflections: {str(e)}")

@router.get("/reflection/search", response_model=List[ReflectionObject])
async def search_reflections(query: str, user_id: str = "default_user", limit: int = 5):
    try:
        store = get_reflection_store()
        return store.search_reflections(query, user_id=user_id, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reflection search failed: {str(e)}")

@router.get("/reflection/summary", response_model=CognitiveProfile)
async def get_cognitive_summary(user_id: str = "default_user"):
    try:
        engine = get_reflection_engine()
        return engine.generate_cognitive_summary(user_id=user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")
