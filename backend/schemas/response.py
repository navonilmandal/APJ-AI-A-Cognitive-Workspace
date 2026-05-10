from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ResponseMetadata(BaseModel):
    route: str
    model: str
    provider: str
    used_memory: bool = False
    used_reflection: bool = False
    complexity_score: float
    confidence: float = 1.0
    fallback_used: bool = False
    latency_ms: Optional[float] = None

class HybridResponse(BaseModel):
    answer: str
    metadata: ResponseMetadata
    grounding_sources: List[str] = Field(default_factory=list)
