"""Common message types for LLM interactions."""
from typing import TypedDict, Dict, Any, List, Optional

class ChatMessage(TypedDict):
    """Generic chat message type compatible with various LLM providers."""
    role: str
    content: str 