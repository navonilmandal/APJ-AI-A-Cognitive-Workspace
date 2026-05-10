import re
from enum import Enum
from typing import Dict, Any

class TaskCategory(Enum):
    MEMORY = "memory"
    REFLECTION = "reflection"
    CODING = "coding"
    REASONING = "reasoning"
    CONVERSATIONAL = "conversational"
    GENERAL = "general"
    RESEARCH = "research"
    GREETING = "greeting"
    INTRODUCTION = "introduction"
    SMALL_TALK = "small_talk"
    MEMORY_QUERY = "memory_query"
    TECHNICAL = "technical"
    PERSONAL_REFLECTION = "personal_reflection"

class TaskRouter:
    """
    Classifies user intent to determine the best reasoning route.
    """
    def __init__(self):
        self.patterns = {
            TaskCategory.GREETING: [
                r"^(hi|hello|hey|hey there|greetings|morning|afternoon|evening)$",
                r"^(good morning|good afternoon|good evening|good night)$",
            ],
            TaskCategory.INTRODUCTION: [
                r"(my name is|i am|call me|i'm|this is) \w+",
                r"(who are you|what is your name|introduce yourself)"
            ],
            TaskCategory.SMALL_TALK: [
                r"(how are you|how's it going|what's up|how are things|what is happening)",
                r"(nice to meet you|glad to be here)"
            ],
            TaskCategory.MEMORY_QUERY: [
                r"(what do you remember|what do you know about me|recall our last conversation)",
                r"(who am i|tell me about myself|summarize my interests)"
            ],
            TaskCategory.PERSONAL_REFLECTION: [
                r"(habit|interest|notice|pattern|trend|personality|preference|tendency)",
                r"(how do i|my style|my tendency|change over time)"
            ],
            TaskCategory.TECHNICAL: [
                r"(deep learning|neural network|architecture|transformer|embedding|vector store)",
                r"(gpu|cuda|inference|latency|optimization|deployment|scalability)",
                r"(ml|machine learning|gradient descent|backpropagation|regression|classification)"
            ],
            TaskCategory.CODING: [
                r"(code|python|script|function|optimize|bug|fix|error|javascript|rust|algorithm)",
                r"(program|develop|snippet|implementation|binary search|sorting)"
            ],
            TaskCategory.RESEARCH: [
                r"(current|news|latest|who is|weather|today|price|event|stock|google|search|real-time)",
                r"(what is happening|recent|updated info|find on web)"
            ],
            TaskCategory.REASONING: [
                r"(explain|why|how does|compare|decide|complex|logic|analyze|pros and cons)",
                r"(step by step|detailed|deep dive|synthesis|reason|syllabus|pdf|deadlock)"
            ],
            TaskCategory.MEMORY: [
                r"(remember|memory|history|past|recall|previous|last time|interactions|told you)"
            ],
        }

    def classify(self, query: str) -> TaskCategory:
        query_lower = query.strip().lower()
        print(f"[DEBUG] Classifying query: {query_lower}")
        
        # Priority 1: Direct greetings (exact match or very short)
        if query_lower in ["hi", "hello", "hey", "hola"]:
            return TaskCategory.GREETING

        for category, regex_list in self.patterns.items():
            for pattern in regex_list:
                if re.search(pattern, query_lower):
                    print(f"[DEBUG] Matched category: {category.value} via pattern: {pattern}")
                    return category
        
        print("[DEBUG] No match found, defaulting to CONVERSATIONAL")
        return TaskCategory.CONVERSATIONAL

def get_task_router():
    return TaskRouter()
