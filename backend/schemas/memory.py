from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime

class MemoryObject(BaseModel):
    """
    Unified memory object for all conversational turns.
    Includes explicit scoping to prevent cross-user contamination.
    """
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_id: str = "default_user"  # Critical for isolation
    memory_type: Literal["personal", "dataset"] = "personal"  # Isolation scope
    conversation_id: str
    speaker: str
    message: str
    source: str
    topic: Optional[str] = None
    emotion: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
