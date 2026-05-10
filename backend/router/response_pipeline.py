import time
import logging
from typing import Optional, List, Dict, Any
from backend.router.task_router import get_task_router, TaskCategory
from backend.router.complexity_estimator import get_complexity_estimator
from backend.router.model_selector import get_model_selector
from backend.models.cloud_llm import get_cloud_llm
from backend.models.local_llm import get_llm_service
from backend.memory.service import MemoryService
from backend.retrieval.service import RetrievalService
from backend.reflection.reflection_engine import ReflectionEngine
from backend.schemas.response import HybridResponse, ResponseMetadata
from backend.models.model_registry import ModelProvider
from backend.models.web_search import WebSearchService

logger = logging.getLogger(__name__)

class ResponsePipeline:
    """
    The orchestration layer of the assistant.
    Coordinates query analysis, retrieval, model selection, and response generation.
    """
    def __init__(
        self,
        memory_service: MemoryService,
        reflection_engine: ReflectionEngine,
    ):
        self.task_router = get_task_router()
        self.complexity_estimator = get_complexity_estimator()
        self.model_selector = get_model_selector()
        self.cloud_llm = get_cloud_llm()
        self.local_llm = get_llm_service()
        self.memory = memory_service
        self.reflection_engine = reflection_engine
        self.web_search = WebSearchService()

    async def execute(self, query: str, user_id: str = "default_user") -> HybridResponse:
        start_time = time.time()
        
        # 1. Analyze query
        category = self.task_router.classify(query)
        complexity = self.complexity_estimator.estimate(query)
        query_word_count = len(query.split())
        
        # 2. Contextual Memory Suppression Logic
        suppress_memories = False
        suppression_reason = None
        
        # Rule A: Explicit categories
        if category in [TaskCategory.GREETING, TaskCategory.INTRODUCTION, TaskCategory.SMALL_TALK]:
            suppress_memories = True
            suppression_reason = f"Intent category {category.value} detected"
            
        # Rule B: Query Length & Complexity Safeguard
        # Only suppress if it's NOT a category that explicitly requires memory
        elif query_word_count < 4 and complexity < 0.1:
            if category not in [TaskCategory.MEMORY_QUERY, TaskCategory.PERSONAL_REFLECTION, TaskCategory.MEMORY]:
                suppress_memories = True
                suppression_reason = f"Low complexity ({complexity}) and short query ({query_word_count} words)"

        print(f"[DEBUG] Detected intent: {category.value}")
        print(f"[DEBUG] Memory suppressed: {suppress_memories}")
        if suppress_memories:
            print(f"[DEBUG] Retrieval skipped reason: {suppression_reason}")

        # 3. Retrieve memory & reflections (if not suppressed)
        memories = []
        reflections = []
        
        if not suppress_memories:
            memories = self.memory.retrieve_context(query, user_id=user_id, limit=5)
            reflections = self.reflection_engine.search_reflections(query, user_id=user_id, limit=3)
        
        context_str = self._format_context(memories, reflections)
        used_memory = len(memories) > 0
        used_reflection = len(reflections) > 0

        # 4. Perform Web Search if needed
        search_context = ""
        if category == TaskCategory.RESEARCH:
            search_context = self.web_search.get_search_context(query)
            if search_context:
                context_str += search_context
        
        # 5. Select reasoning route
        model_id, provider = self.model_selector.select_model(category, complexity)
        
        # 6. Generate response
        system_prompt = self._build_system_prompt(category, context_str)
        
        answer = None
        fallback_used = False
        
        try:
            if provider == ModelProvider.LOCAL.value:
                answer = await self._call_local(query, system_prompt)
            else:
                answer = await self.cloud_llm.generate(provider, model_id, query, system_prompt)
                
            if not answer:
                raise RuntimeError(f"Model {model_id} via {provider} returned empty response.")
                
        except Exception as e:
            logger.error(f"Primary route failed: {e}. Attempting fallback...")
            fallback_used = True
            model_id, provider = self.model_selector.get_fallback(model_id)
            
            if provider == ModelProvider.LOCAL.value:
                answer = await self._call_local(query, system_prompt)
            else:
                answer = await self.cloud_llm.generate(provider, model_id, query, system_prompt)

        # 7. Synthesis & Validation
        if not answer:
            answer = "I'm sorry, I'm having trouble processing your request right now. I can still access your memories, but my reasoning engine is currently unavailable."
            
        latency = (time.time() - start_time) * 1000
        
        # 8. Build final response
        # Map specific greeting/small talk intents to 'conversational' route for metadata
        display_route = category.value
        if category in [TaskCategory.GREETING, TaskCategory.INTRODUCTION, TaskCategory.SMALL_TALK]:
            display_route = TaskCategory.CONVERSATIONAL.value

        metadata = ResponseMetadata(
            route=display_route,
            model=model_id,
            provider=provider,
            used_memory=used_memory,
            used_reflection=used_reflection,
            complexity_score=complexity,
            confidence=0.9, # Placeholder
            fallback_used=fallback_used,
            latency_ms=latency
        )
        
        sources = [str(m.id) for m in memories] + [str(r.reflection_id) for r in reflections]
        
        return HybridResponse(
            answer=answer,
            metadata=metadata,
            grounding_sources=sources
        )

    def _format_context(self, memories, reflections) -> str:
        context_parts = []
        if memories:
            context_parts.append("Relevant past interactions:")
            for m in memories:
                context_parts.append(f"- {m.message}")
        if reflections:
            context_parts.append("\nRelevant cognitive reflections about you:")
            for r in reflections:
                context_parts.append(f"- {r.insight} (Confidence: {r.confidence})")
        
        return "\n".join(context_parts)

    def _build_system_prompt(self, category: TaskCategory, context: str) -> str:
        base_prompt = "You are an intelligent cognitive assistant."
        
        if context:
            base_prompt += f"\n\nYou have access to the user's semantic memory and personality reflections:\n{context}\n"
        else:
            base_prompt += "\nNo relevant personal memories were injected for this query to maintain a natural conversation flow."
        
        if category == TaskCategory.GREETING:
            base_prompt += "\nYou are in GREETING mode. Keep it brief, friendly, and natural. Do not mention deep technical interests or past history unless asked."
        elif category == TaskCategory.INTRODUCTION:
            base_prompt += "\nYou are in INTRODUCTION mode. Acknowledge the user's introduction warmly."
        elif category == TaskCategory.SMALL_TALK:
            base_prompt += "\nYou are in SMALL_TALK mode. Be engaging and polite, but keep the focus on the current interaction."
        elif category == TaskCategory.MEMORY_QUERY:
            base_prompt += "\nYou are in MEMORY retrieval mode. The user is explicitly asking about what you know. Use the provided context to answer accurately."
        elif category == TaskCategory.TECHNICAL:
            base_prompt += "\nYou are in TECHNICAL mode. Provide precise, expert-level information on the technical topic."
        elif category == TaskCategory.PERSONAL_REFLECTION:
            base_prompt += "\nYou are in PERSONAL REFLECTION mode. Discuss the user's patterns, habits, or tendencies based on the provided context."
        elif category == TaskCategory.CODING:
            base_prompt += "\nYou are currently in CODING mode. Provide optimized, clean, and well-documented code."
        elif category == TaskCategory.REASONING:
            base_prompt += "\nYou are currently in DEEP REASONING mode. Provide detailed, step-by-step analysis."
        elif category == TaskCategory.RESEARCH:
            base_prompt += "\nYou are currently in RESEARCH mode. Use the provided real-time web search results to answer questions about current events or facts. Cite the sources if possible."
            
        base_prompt += "\nAlways maintain a helpful, professional, and personality-aware tone."
        return base_prompt

    async def _call_local(self, query: str, system_prompt: str) -> str:
        # Wrap the synchronous generate in a thread pool to avoid blocking async loop
        import asyncio
        from functools import partial
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            partial(self.local_llm.generate, prompt=query, system_prompt=system_prompt)
        )

def get_response_pipeline(memory_service: MemoryService, reflection_engine: ReflectionEngine):
    return ResponsePipeline(memory_service, reflection_engine)
