"""
Shared data models for LLM composition patterns.

This module contains Pydantic models shared across different patterns
to ensure consistency and reduce duplication.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ProductData(BaseModel):
    """Product data model for use across different patterns."""
    id: int
    name: str
    features: str = ""
    details: str = ""
    fabric_details: str = ""
    other_details: str = ""
    price: str = ""
    colors: List[str] = Field(default_factory=list)
    sizes: List[str] = Field(default_factory=list)


class EvaluationCriteria(BaseModel):
    """Individual evaluation criterion with score and feedback."""
    name: str
    score: int = 0  # Typically 0-10 or similar scale
    feedback: str = ""
    
    def is_passing(self, threshold: int = 7) -> bool:
        """Check if this criterion meets the passing threshold."""
        return self.score >= threshold


class EvaluationResult(BaseModel):
    """Evaluation result model for patterns that assess content quality."""
    status: str = "NEEDS_IMPROVEMENT"  # "PASS" or "NEEDS_IMPROVEMENT"
    feedback: str = ""
    criteria: List[EvaluationCriteria] = Field(default_factory=list)
    
    def is_successful(self) -> bool:
        """Check if the evaluation passed."""
        return self.status == "PASS" 