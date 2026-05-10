import json
import re
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from qdrant_client import models
from backend.models.local_llm import get_llm_service
from backend.memory.vector_store import get_vector_store
from backend.reflection.schemas import ReflectionObject, Evidence, CognitiveProfile
from backend.reflection.reflection_store import get_reflection_store
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

class ReflectionEngine:
    """
    High-Reliability Reflection Engine for Small Models.
    Uses Line-Based JSON (JSONL) to prevent parser crashes on punctuation errors.
    """
    def __init__(self):
        self.llm = get_llm_service()
        self.memory_store = get_vector_store()
        self.reflection_store = get_reflection_store()

    def run_reflection_cycle(self, user_id: str = "default_user", query: Optional[str] = None):
        logger.info(f"Starting Line-Based Reflection Cycle for User: {user_id}")
        
        search_query = query or "user behavior, preferences, and emotions"
        
        query_filter = models.Filter(
            must=[
                models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
                models.FieldCondition(key="memory_type", match=models.MatchValue(value="personal"))
            ]
        )
        
        hits = self.memory_store.client.scroll(
            collection_name=self.memory_store.collection_name,
            scroll_filter=query_filter,
            limit=20,
            with_payload=True
        )[0]
        
        if not hits:
            return []

        raw_memories = [{"id": h.id, "text": h.payload['message'], "speaker": h.payload['speaker']} for h in hits]
        existing_reflections = self.reflection_store.search_reflections(search_query, user_id=user_id, limit=5)
        
        all_insights = []
        for ref_type in ["habit", "interest", "emotional_trend"]:
            insights = self._generate_jsonl_reflections(user_id, ref_type, raw_memories, existing_reflections)
            all_insights.extend(insights)

        for insight in all_insights:
            self.reflection_store.save_reflection(insight)
            
        return all_insights

    def _generate_jsonl_reflections(self, user_id: str, ref_type: str, memories: List[Dict], existing: List[ReflectionObject]) -> List[ReflectionObject]:
        existing_context = "\n".join([f"- [ID:{r.reflection_id}] {r.insight}" for r in existing if r.type == ref_type])
        memory_str = "\n".join([f"- [MEM:{m['id']}] {m['speaker']}: {m['text']}" for m in memories])

        prompt = (
            f"Analyze user memories for {ref_type}s.\n\n"
            f"--- EXISTING ---\n{existing_context or 'None'}\n\n"
            f"--- MEMORIES ---\n{memory_str}\n\n"
            f"--- TASK ---\n"
            f"1. Identify new patterns or update existing IDs.\n"
            f"2. Output EACH insight as a single JSON line. DO NOT use a list [].\n"
            f"Format: {{\"id\": \"...\", \"insight\": \"...\", \"confidence\": 0.X, \"evidence\": [\"mem_id\"]}}\n"
            f"3. Be concise. Only output 1-3 lines.\n"
            f"\nResult (JSON Lines):"
        )

        try:
            response = self.llm.generate(prompt, system_prompt="You output raw JSON lines only. No lists, no text.")
            
            reflections = []
            for line in response.strip().split('\n'):
                line = line.strip()
                if not line or not (line.startswith('{') and line.endswith('}')):
                    continue
                
                try:
                    # Clean up common small errors (like trailing commas inside the line)
                    line = re.sub(r',\s*}', '}', line)
                    item = json.loads(line)
                    
                    ref_id = item.get("id")
                    if not ref_id or ref_id == "NEW" or "ref_" in str(ref_id):
                        ref_id = str(uuid.uuid4())
                    
                    evidence_list = []
                    for eid in item.get("evidence", []):
                        clean_id = str(eid).replace("MEM:", "").replace("ID:", "").strip()
                        m_match = next((m for m in memories if str(m['id']) == clean_id), None)
                        if m_match:
                            evidence_list.append(Evidence(memory_id=clean_id, text=m_match['text']))

                    if not evidence_list: continue

                    reflections.append(ReflectionObject(
                        reflection_id=ref_id,
                        user_id=user_id,
                        type=ref_type,
                        insight=item["insight"],
                        confidence=item["confidence"],
                        evidence=evidence_list
                    ))
                except Exception as je:
                    logger.warning(f"Skipping malformed JSON line: {je} | Line: {line[:50]}...")
                    continue
                    
            return reflections
        except Exception as e:
            logger.error(f"JSONL Reflection failed: {e}")
            return []

    def generate_cognitive_summary(self, user_id: str = "default_user") -> CognitiveProfile:
        """
        Synthesizes all stored reflections into a coherent cognitive profile.
        """
        logger.info(f"Synthesizing Cognitive Profile for User: {user_id}")
        
        # 1. Fetch all reflections for this user
        reflections = self.reflection_store.get_reflections(user_id=user_id, limit=50)
        
        if not reflections:
            return CognitiveProfile(
                user_id=user_id,
                overview="No cognitive insights yet.",
                core_interests=[], behavioral_habits=[], evolving_opinions=[], 
                emotional_trends=[], long_term_goals=[], confidence_metrics={}, evidence_count=0
            )

        # 2. Build Synthesis Prompt
        ref_context = "\n".join([f"- [{r.type.upper()}] {r.insight} (Strength: {r.strength}, Confidence: {r.confidence})" for r in reflections])
        
        prompt = (
            f"You are a Senior Cognitive Scientist. Synthesize a unified Mental Model for {user_id}.\n\n"
            f"--- COGNITIVE INSIGHTS ---\n{ref_context}\n\n"
            f"--- TASK ---\n"
            f"1. Create a 3-sentence 'User Overview'.\n"
            f"2. Group insights into Core Interests, Habits, Evolving Opinions, Emotional Trends, and Goals.\n"
            f"3. Be evidence-based and use cautious language for weak insights.\n"
            f"4. Output ONLY a raw JSON object matching the CognitiveProfile schema.\n"
            f"Schema: {{\"overview\": \"...\", \"core_interests\": [], \"behavioral_habits\": [], \"evolving_opinions\": [], \"emotional_trends\": [], \"long_term_goals\": []}}\n"
            f"\nResult (JSON ONLY):"
        )

        try:
            response = self.llm.generate(prompt, system_prompt="You are a clinical psychologist synthesizing user data. Output valid JSON.")
            
            # Use robust extraction
            start = response.find('{')
            end = response.rfind('}')
            if start == -1: raise ValueError("No JSON found in response")
            
            data = json.loads(response[start:end+1])
            
            return CognitiveProfile(
                user_id=user_id,
                overview=data.get("overview", "No overview generated."),
                core_interests=data.get("core_interests", []),
                behavioral_habits=data.get("behavioral_habits", []),
                evolving_opinions=data.get("evolving_opinions", []),
                emotional_trends=data.get("emotional_trends", []),
                long_term_goals=data.get("long_term_goals", []),
                confidence_metrics={"average": sum(r.confidence for r in reflections)/len(reflections)},
                evidence_count=sum(r.evidence_count for r in reflections)
            )
        except Exception as e:
            logger.error(f"Cognitive synthesis failed: {e}")
            raise e

    def search_reflections(self, query: str, user_id: str = "default_user", limit: int = 3) -> List[ReflectionObject]:
        """
        Wrapper to semantically retrieve reflections for the response pipeline.
        """
        return self.reflection_store.search_reflections(query, user_id=user_id, limit=limit)

# Singleton
_engine = None
def get_reflection_engine():
    global _engine
    if _engine is None:
        _engine = ReflectionEngine()
    return _engine
