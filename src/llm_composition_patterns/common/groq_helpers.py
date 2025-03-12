"""Simple helper for Groq LLM API interactions."""
import os
from typing import Optional, List, Dict, Any

from groq import Groq
from dotenv import load_dotenv
from llm_composition_patterns.common.message_types import ChatMessage

load_dotenv()

def run_llm(
    user_prompt: str, 
    model: str = "llama-3.3-70b-versatile", 
    system_prompt: Optional[str] = None,
    message_history: Optional[List[ChatMessage]] = None
):
    """
    Run a Groq LLM with the given prompts and optional message history.
    
    Args:
        user_prompt: The prompt to send to the LLM
        model: The Groq model to use
        system_prompt: Optional system prompt to set context
        message_history: Optional list of previous messages in the conversation
        
    Returns:
        The LLM's response text
    """
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    # Type annotation for mypy, but using a regular list at runtime
    messages: Any = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    # Add message history if provided
    if message_history:
        messages.extend(message_history)
    
    # Add the current user prompt
    messages.append({"role": "user", "content": user_prompt})
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=4000,        
    )

    return response.choices[0].message.content
