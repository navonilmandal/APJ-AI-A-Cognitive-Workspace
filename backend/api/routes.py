from fastapi import APIRouter, HTTPException, Query, Depends, Request
from typing import List, Optional, Dict, Any
from backend.memory.vector_store import get_vector_store
from backend.memory.qdrant_client import get_qdrant_client
from backend.reflection.reflection_engine import get_reflection_engine
from backend.reflection.reflection_store import get_reflection_store
from backend.reflection.schemas import ReflectionObject, CognitiveProfile
from backend.schemas.memory import MemoryObject
from backend.utils.logger import setup_logger
from backend.utils.security_utils import scan_prompt_injection, sanitize_input

from backend.router.response_pipeline import get_response_pipeline
from backend.memory.service import get_memory_service
from backend.schemas.response import HybridResponse
from backend.auth.routes import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = setup_logger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

from backend.schemas.chat import ChatRequest

@router.post("/chat", response_model=HybridResponse)
@limiter.limit("20/minute")
async def chat_query(request: Request, chat_request: ChatRequest, current_user: str = Depends(get_current_user)):
    try:
        # Security: Sanitize input
        clean_query = sanitize_input(chat_request.query)
        
        # Security: Prompt Injection Check
        is_malicious, pattern = scan_prompt_injection(clean_query)
        if is_malicious:
            logger.warning(f"Security Alert: Blocked prompt injection from user {current_user}")
            # Log to security log
            with open("logs/security.log", "a") as f:
                f.write(f"{chat_request.query} | User: {current_user} | Pattern: {pattern}\n")
            raise HTTPException(status_code=400, detail="Potential security threat detected in query.")

        memory_service = get_memory_service()
        reflection_engine = get_reflection_engine()
        pipeline = get_response_pipeline(memory_service, reflection_engine)
        
        # Security: Ensure user_id matches authenticated user
        response = await pipeline.execute(clean_query, user_id=current_user)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "cognitive-assistant-v2"}

@router.post("/memory/ingest")
async def ingest_memory(memories: List[MemoryObject], current_user: str = Depends(get_current_user)):
    try:
        store = get_vector_store()
        # Security: Force user_id to match current_user for all memories
        for m in memories:
            m.user_id = current_user
        store.upsert_memories(memories)
        return {"status": "success", "count": len(memories)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.get("/memory/search")
async def search_memory(query: str, limit: int = 5, current_user: str = Depends(get_current_user)):
    try:
        store = get_vector_store()
        return store.search(query, user_id=current_user, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/reflection/generate", response_model=List[ReflectionObject])
async def generate_reflections(query: Optional[str] = None, current_user: str = Depends(get_current_user)):
    try:
        engine = get_reflection_engine()
        return engine.run_reflection_cycle(user_id=current_user, query=query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reflection cycle failed: {str(e)}")

@router.get("/reflection/list", response_model=List[ReflectionObject])
async def list_reflections(type: Optional[str] = None, 
                           min_strength: Optional[str] = Query(None, pattern="^(weak|medium|strong)$"),
                           limit: int = 20,
                           current_user: str = Depends(get_current_user)):
    try:
        store = get_reflection_store()
        return store.get_reflections(user_id=current_user, reflection_type=type, min_strength=min_strength, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch reflections: {str(e)}")

@router.get("/reflection/search", response_model=List[ReflectionObject])
async def search_reflections(query: str, limit: int = 5, current_user: str = Depends(get_current_user)):
    try:
        store = get_reflection_store()
        return store.search_reflections(query, user_id=current_user, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reflection search failed: {str(e)}")

@router.get("/reflection/summary", response_model=CognitiveProfile)
async def get_cognitive_summary(current_user: str = Depends(get_current_user)):
    try:
        engine = get_reflection_engine()
        return engine.generate_cognitive_summary(user_id=current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

