import logging
from typing import Optional, Tuple
from backend.models.model_registry import ModelConfig, ModelProvider, ModelCapability, get_models_by_capability, MODEL_REGISTRY
from backend.router.task_router import TaskCategory
from backend.core.config import settings

logger = logging.getLogger(__name__)

class ModelSelector:
    """
    Intelligently selects the best model for a given task and complexity.
    """
    def __init__(self):
        self.fallback_model_id = "qwen2.5-3b"

    def select_model(self, category: TaskCategory, complexity: float) -> Tuple[str, str]:
        """
        Returns (model_id, provider)
        """
        # Mapping TaskCategory to ModelCapability
        if category == TaskCategory.MEMORY or category == TaskCategory.REFLECTION:
            return "qwen2.5-3b", ModelProvider.LOCAL.value
            
        if category == TaskCategory.CODING:
            if settings.GROQ_API_KEY:
                return "llama-3.3-70b-groq", ModelProvider.GROQ.value
            elif settings.OPENROUTER_API_KEY:
                return "openrouter-premium", ModelProvider.OPENROUTER.value
            elif settings.GEMINI_API_KEY:
                return "gemini-1.5-flash", ModelProvider.GEMINI.value
                
        if category == TaskCategory.RESEARCH:
            if settings.GEMINI_API_KEY:
                return "gemini-1.5-flash", ModelProvider.GEMINI.value
            elif settings.GROQ_API_KEY:
                return "llama-3.3-70b-groq", ModelProvider.GROQ.value

        if complexity > settings.COMPLEXITY_THRESHOLD:
            # Prefer Gemini for high complexity, then Groq
            if settings.GEMINI_API_KEY:
                return "gemini-1.5-flash", ModelProvider.GEMINI.value
            elif settings.GROQ_API_KEY:
                return "llama-3.3-70b-groq", ModelProvider.GROQ.value
            elif settings.OPENROUTER_API_KEY:
                return "openrouter-premium", ModelProvider.OPENROUTER.value
        
        # Low complexity or conversational
        if complexity > 0.3: # Mid-range
            if settings.GROQ_API_KEY:
                return "llama-3.1-8b-groq", ModelProvider.GROQ.value
                
        # Default for low complexity/general
        return "qwen2.5-3b", ModelProvider.LOCAL.value

    def get_fallback(self, failed_model_id: str) -> Tuple[str, str]:
        """
        Returns a fallback model if the primary choice fails.
        Sequential fallback chain: Gemini -> Groq -> OpenRouter -> Local
        """
        logger.warning(f"Fallback triggered for model: {failed_model_id}")
        
        # Determine the provider of the failed model
        failed_config = MODEL_REGISTRY.get(failed_model_id)
        failed_provider = failed_config.provider if failed_config else ModelProvider.LOCAL
        
        if not failed_config:
            logger.error(f"Failed model {failed_model_id} not found in registry. Defaulting to LOCAL fallback.")
            return self.fallback_model_id, ModelProvider.LOCAL.value
        
        # 1. If Gemini failed, try Groq
        if failed_provider == ModelProvider.GEMINI:
            if settings.GROQ_API_KEY:
                return "llama-3.3-70b-groq", ModelProvider.GROQ.value
            elif settings.OPENROUTER_API_KEY:
                return "openrouter-fallback", ModelProvider.OPENROUTER.value
            return "qwen2.5-3b", ModelProvider.LOCAL.value
            
        # 2. If Groq failed, try OpenRouter
        if failed_provider == ModelProvider.GROQ:
            if settings.OPENROUTER_API_KEY:
                return "openrouter-fallback", ModelProvider.OPENROUTER.value
            elif settings.GEMINI_API_KEY:
                return "gemini-1.5-flash", ModelProvider.GEMINI.value
            return "qwen2.5-3b", ModelProvider.LOCAL.value
            
        # 3. If OpenRouter failed, try Local
        if failed_provider == ModelProvider.OPENROUTER:
            return "qwen2.5-3b", ModelProvider.LOCAL.value
            
        # 4. If Local failed, try any available cloud as last resort
        if failed_provider == ModelProvider.LOCAL:
            if settings.GEMINI_API_KEY:
                return "gemini-1.5-flash", ModelProvider.GEMINI.value
            elif settings.GROQ_API_KEY:
                return "llama-3.1-8b-groq", ModelProvider.GROQ.value
                
        return "qwen2.5-3b", ModelProvider.LOCAL.value

def get_model_selector():
    return ModelSelector()
