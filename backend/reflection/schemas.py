from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class Evidence(BaseModel):
    """Supporting evidence for a reflection."""
    memory_id: str
    text: str

class ReflectionObject(BaseModel):
    """
    An evolving cognitive insight.
    Includes user_id to ensure strict identity isolation.
    """
    reflection_id: str
    user_id: str = "default_user"  # NEW: Identity Isolation
    type: Literal["habit", "interest", "emotional_trend", "goal", "other"]
    insight: str
    strength: Literal["weak", "medium", "strong"] = "weak"
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_count: int = 0
    evidence: List[Evidence] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ReflectionUpdate(BaseModel):
    """Input for updating an existing reflection."""
    new_evidence: List[Evidence]
    added_confidence: float

class CognitiveProfile(BaseModel):
    """
    A synthesized mental model of the user.
    Combines interests, habits, evolution, and goals.
    """
    user_id: str
    overview: str
    core_interests: List[str]
    behavioral_habits: List[str]
    evolving_opinions: List[str]
    emotional_trends: List[str]
    long_term_goals: List[str]
    confidence_metrics: dict = {}
    evidence_count: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)
