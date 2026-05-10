from typing import Dict, Any

class ComplexityEstimator:
    """
    Estimates the reasoning depth required for a query.
    Score: 0.0 (Simple) to 1.0 (Deep Reasoning).
    """
    def __init__(self):
        self.heavy_keywords = [
            "detail", "step by step", "comprehensive", "advanced", 
            "architect", "optimization", "complex", "analyze", 
            "compare", "pros and cons", "synthesis", "deep dive",
            "gradient descent", "backpropagation", "loss function",
            "calculus", "probability", "statistics", "mathematics",
            "ml", "machine learning"
        ]
        self.planning_keywords = ["plan", "strategy", "roadmap", "schedule", "how should i"]
        self.coding_intent = ["code", "script", "refactor", "debug", "implement"]
        self.academic_keywords = ["example", "exercise", "problem", "hard", "tutorial", "explain"]

    def estimate(self, query: str) -> float:
        score = 0.0
        query_lower = query.lower()
        
        # 1. Length based
        if len(query) > 300:
            score += 0.4
        elif len(query) > 150:
            score += 0.2
        elif len(query) > 50:
            score += 0.1 # Small boost for medium length
            
        # 2. Keyword based (Reasoning Depth)
        for word in self.heavy_keywords:
            if word in query_lower:
                score += 0.25 # Increased from 0.15
                
        # 3. Planning & Academic Requirements
        for word in self.planning_keywords + self.academic_keywords:
            if word in query_lower:
                score += 0.2
                
        # 4. Multi-step reasoning indicators
        multi_step_indicators = ["first", "then", "finally", "after that", "multiple steps", "3", "4", "three", "four"]
        if any(indicator in query_lower for indicator in multi_step_indicators):
            score += 0.2
            
        # 5. Question depth indicators
        depth_indicators = ["why", "how", "contrast", "differentiate", "describe"]
        if any(q in query_lower for q in depth_indicators):
            score += 0.15
            
        return min(1.0, score)

def get_complexity_estimator():
    return ComplexityEstimator()
