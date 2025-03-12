"""Simple helper for Fireworks LLM API interactions."""
import os
from typing import Optional, List, Dict, Any, cast
from fireworks.client import Fireworks
from dotenv import load_dotenv
from llm_composition_patterns.common.message_types import ChatMessage

load_dotenv()

def run_llm(
    user_prompt: str, 
    model: str = "accounts/fireworks/models/llama-v3p3-70b-instruct", 
    system_prompt: Optional[str] = None,
    message_history: Optional[List[ChatMessage]] = None
):
    """
    Run a Fireworks LLM with the given prompts and optional message history.
    
    Args:
        user_prompt: The prompt to send to the LLM
        model: The Fireworks model to use
        system_prompt: Optional system prompt to set context
        message_history: Optional list of previous messages in the conversation
        
    Returns:
        The LLM's response text
    """
    client = Fireworks(api_key=os.environ.get("FIREWORKS_API_KEY"))
    
    messages: Any = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    # Add message history if provided
    if message_history:
        # Use type casting to satisfy the type checker
        messages.extend(cast(List[Dict[str, str]], message_history))
    
    # Add the current user prompt
    messages.append({"role": "user", "content": user_prompt})
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=4000,        
    )

    return response.choices[0].message.content