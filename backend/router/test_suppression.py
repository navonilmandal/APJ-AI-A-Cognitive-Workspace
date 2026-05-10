import os
import sys
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).resolve().parent.parent.parent
if str(root) not in sys.path:
    sys.path.append(str(root))

import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock
from backend.router.task_router import TaskRouter, TaskCategory
from backend.router.response_pipeline import ResponsePipeline
from backend.router.complexity_estimator import ComplexityEstimator

class TestMemorySuppression(unittest.TestCase):
    def setUp(self):
        self.router = TaskRouter()
        self.complexity = ComplexityEstimator()
        
    def test_intent_classification(self):
        test_cases = [
            ("hi", TaskCategory.GREETING),
            ("hello", TaskCategory.GREETING),
            ("good morning", TaskCategory.GREETING),
            ("my name is navonil", TaskCategory.INTRODUCTION),
            ("how are you", TaskCategory.SMALL_TALK),
            ("what do you remember about me?", TaskCategory.MEMORY_QUERY),
            ("help me learn deep learning", TaskCategory.TECHNICAL),
            ("what is my personality pattern?", TaskCategory.PERSONAL_REFLECTION),
            ("write a python script", TaskCategory.CODING),
            ("explain quantum computing", TaskCategory.REASONING),
        ]
        
        for query, expected_category in test_cases:
            with self.subTest(query=query):
                category = self.router.classify(query)
                self.assertEqual(category, expected_category)

    def test_suppression_logic(self):
        def should_suppress(query):
            category = self.router.classify(query)
            complexity = self.complexity.estimate(query)
            word_count = len(query.split())
            
            if category in [TaskCategory.GREETING, TaskCategory.INTRODUCTION, TaskCategory.SMALL_TALK]:
                return True, "Intent"
            if word_count < 4 and complexity < 0.1:
                if category not in [TaskCategory.MEMORY_QUERY, TaskCategory.PERSONAL_REFLECTION, TaskCategory.MEMORY]:
                    return True, "Short/Simple"
            return False, None

        suppress_cases = [
            ("hi", True),
            ("hello", True),
            ("my name is navonil", True),
            ("how are you", True),
            ("good morning", True),
            ("What's up?", True),
            ("yo", True), 
        ]
        
        for query, expected_suppress in suppress_cases:
            with self.subTest(query=query):
                suppressed, _ = should_suppress(query)
                self.assertEqual(suppressed, expected_suppress)

        active_cases = [
            ("What do you know about me?", False),
            ("Help me learn deep learning.", False),
            ("Summarize my interests.", False),
            ("How should I study deep learning architecture for production?", False),
        ]
        
        for query, expected_suppress in active_cases:
            with self.subTest(query=query):
                suppressed, _ = should_suppress(query)
                self.assertEqual(suppressed, expected_suppress)

if __name__ == "__main__":
    unittest.main()
