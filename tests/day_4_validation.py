import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.router.task_router import get_task_router, TaskCategory
from backend.router.complexity_estimator import get_complexity_estimator
from backend.router.model_selector import get_model_selector
from backend.models.model_registry import ModelProvider
from backend.router.response_pipeline import get_response_pipeline
from backend.memory.service import get_memory_service
from backend.reflection.reflection_engine import get_reflection_engine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Validation")

async def run_validation():
    logger.info("=== Starting Day 4 Integration Validation ===")
    
    # 1. Component Initialization
    try:
        router = get_task_router()
        estimator = get_complexity_estimator()
        selector = get_model_selector()
        memory = get_memory_service()
        reflection = get_reflection_engine()
        pipeline = get_response_pipeline(memory, reflection)
        logger.info("✅ All core components initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        return

    # 2. Task Routing Validation
    test_queries = {
        "What are my study habits?": TaskCategory.REFLECTION,
        "Explain deadlocks in detail.": TaskCategory.REASONING,
        "Write a Python script to sort a list.": TaskCategory.CODING,
        "Remember that I like tea.": TaskCategory.MEMORY,
        "Hello there!": TaskCategory.CONVERSATIONAL
    }
    
    for query, expected in test_queries.items():
        category = router.classify(query)
        if category == expected:
            logger.info(f"✅ Route Success: '{query}' -> {category.value}")
        else:
            logger.warning(f"⚠️ Route Mismatch: '{query}' -> {category.value} (Expected: {expected.value})")

    # 3. Complexity Estimation Validation
    complex_query = "Explain the difference between a mutex and a semaphore in detail with a step by step example."
    simple_query = "Hi."
    
    c_score = estimator.estimate(complex_query)
    s_score = estimator.estimate(simple_query)
    
    logger.info(f"📊 Complexity Scores: High={c_score:.2f}, Low={s_score:.2f}")
    if c_score > s_score:
        logger.info("✅ Complexity Estimator correctly ranked queries.")
    else:
        logger.error("❌ Complexity Estimator failed ranking.")

    # 4. Model Selection Validation
    # Case: Coding
    model, provider = selector.select_model(TaskCategory.CODING, 0.5)
    logger.info(f"🤖 Coding Selection: {model} via {provider}")
    
    # Case: High Complexity Reasoning
    model, provider = selector.select_model(TaskCategory.REASONING, 0.9)
    logger.info(f"🤖 High Complexity Selection: {model} via {provider}")

    # 5. Fallback System Validation
    fallback_model, fallback_provider = selector.get_fallback("gemini-1.5-flash")
    logger.info(f"🛡️ Fallback for Gemini: {fallback_model} via {fallback_provider}")
    if fallback_provider == ModelProvider.LOCAL.value:
        logger.info("✅ Fallback correctly defaulted to Local model.")

    # 6. Pipeline Dry Run (Local Only to avoid API usage)
    # We'll use a simple query that should route to local
    try:
        logger.info("🚀 Running local pipeline dry run...")
        response = await pipeline.execute("Tell me about my habits.")
        logger.info(f"📝 Response Metadata: {response.metadata.model_dump()}")
        logger.info(f"💬 Answer Snippet: {response.answer[:100]}...")
        logger.info("✅ Pipeline execution successful.")
    except Exception as e:
        logger.error(f"❌ Pipeline execution failed: {e}")

    logger.info("=== Validation Complete ===")

if __name__ == "__main__":
    asyncio.run(run_validation())
