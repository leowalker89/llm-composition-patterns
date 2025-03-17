"""
Example of prompt chaining for KETL Mtn. Apparel customer service.

This module demonstrates a 3-step prompt chaining pattern:
1. Query validation using Llama 3 Guard
2. Product information lookup from external JSON file
3. Response formatting according to brand voice from external text file
"""

import os
import json
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

# Add these lines to enable tracing
from llm_composition_patterns.common.arize_phoenix_setup import enable_tracing_for_pattern
from opentelemetry import trace  # type: ignore

# Enable tracing for this pattern - must be done before importing any modules that use Groq
tracer_provider = enable_tracing_for_pattern("prompt_chaining")  # type: ignore
tracer = trace.get_tracer("prompt_chaining")  # type: ignore  # Get a tracer for creating spans

# Now import the rest of the modules
from llm_composition_patterns.common.groq_helpers import run_llm
from llm_composition_patterns.common.message_types import ChatMessage




def load_product_data() -> List[Dict]:
    """
    Load product data from the JSON file.
    
    Returns:
        List of product dictionaries
    """
    json_path = Path(__file__).parent.parent.parent / "common" / "ketlmtn_data" / "ketlmtn_products.json"
    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading product data: {e}")
        return []


def load_brand_voice() -> str:
    """
    Load brand voice guidelines from text file.
    
    Returns:
        String containing brand voice guidelines
    """
    voice_path = Path(__file__).parent.parent.parent / "common" / "ketlmtn_data" / "brand_voice.txt"
    try:
        with open(voice_path, "r") as f:
            return f.read()
    except FileNotFoundError as e:
        print(f"Error loading brand voice: {e}")
        return ""


def step1_filter_query_relevance(user_query: str) -> Tuple[bool, str]:
    """
    Filter the query to determine if it's relevant to KETL Mtn. products.
    
    Args:
        user_query: The customer's question or request
        
    Returns:
        Tuple containing:
            - Boolean indicating if query is relevant
            - Explanation message
    """
    system_prompt = """
    You are a query relevance filter for KETL Mtn. Apparel, an outdoor gear company specializing in 
    lightweight, packable, breathable, and durable products for adventure and travel.
    
    Your task is to determine if a customer query is related to KETL Mtn. products, 
    services, outdoor activities, or general information about the company.
    
    ONLY respond with one of these options:
    - "relevant" - if the query is related to KETL Mtn. products, outdoor activities, or appropriate
    - "not relevant" - if the query is inappropriate or completely unrelated to outdoor gear
    
    Relevant queries include:
    - Questions about KETL Mtn. products (hats, tops, shorts, pants, etc.)
    - Questions about product features, materials, or pricing
    - Questions about the company's values or practices
    - Questions about outdoor activities like hiking, biking, camping, travel
    - Questions about product recommendations for specific activities or conditions
    
    BE PERMISSIVE - if the query could reasonably be interpreted as related to outdoor 
    activities or apparel, consider it relevant.
    """
    
    user_prompt = f"Is this query relevant to KETL Mtn. Apparel or outdoor activities? '{user_query}'"
    
    response = run_llm(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model="llama-3.1-8b-instant"  # Using Llama Guard for content moderation
    )
    
    # Clean up response and check if relevant
    response_text = response.strip().lower()
    
    if "relevant" in response_text and "not relevant" not in response_text:
        return True, "Query is related to outdoor apparel or activities."
    else:
        return False, "Query does not appear to be related to KETL Mtn. products or outdoor activities."


def step2_lookup_product_info(user_query: str, conversation_history: Optional[List[ChatMessage]] = None) -> str:
    """
    Look up relevant product information based on the user query.
    
    Args:
        user_query: The customer's question
        conversation_history: Optional list of previous messages
        
    Returns:
        String with detailed answer based on product information
    """
    system_prompt = """
    You are a product information specialist for KETL Mtn. Apparel.
    Given a customer query and the product database, provide a detailed and accurate
    answer to their question based on the product information available.
    
    Be thorough and specific in your response, mentioning relevant product details,
    features, materials, and pricing when applicable.
    
    If the customer is referring to previous messages in the conversation,
    use that context to provide a more relevant answer.
    """
    
    # Load product data from JSON file
    product_data = load_product_data()
    
    # Convert product data to a string format that can be included in the prompt
    product_data_str = json.dumps(product_data, indent=2)
    
    user_prompt = f"""
    Customer query: '{user_query}'
    
    Product database:
    {product_data_str}
    
    Based on this information, provide a detailed answer to the customer's query.
    Reference the product catalog to ensure accuracy.
    """
    
    response = run_llm(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model="llama-3.3-70b-versatile",  # Using more capable model for information retrieval
        message_history=conversation_history
    )
    
    return response


def step3_brand_format_response(product_info: str) -> str:
    """
    Format the response according to KETL Mtn.'s brand voice.
    
    Args:
        product_info: String with detailed product information answer
        
    Returns:
        Formatted response in the company's brand voice
    """
    # Load brand voice guidelines
    brand_voice = load_brand_voice()
    
    system_prompt = f"""
    You are the voice of KETL Mtn. Apparel, an outdoor gear company known for 
    lightweight, packable, breathable, and durable products designed for adventure and travel.
    
    Use the following brand voice guidelines to craft your response:
    
    {brand_voice}
    
    EXTREMELY IMPORTANT: Your responses MUST be very short and concise.
    - Maximum 1-2 short paragraphs
    - Absolute maximum of 50-75 words total
    - Focus only on directly answering the question
    - Include only the most essential product details
    - Use casual, conversational language
    - Avoid lengthy explanations
    
    Rewrite the provided product information in KETL Mtn.'s brand voice,
    but keep it extremely brief and to the point.
    """
    
    user_prompt = f"""
    Original product information:
    {product_info}
    
    Rewrite this in KETL Mtn.'s brand voice, making it EXTREMELY concise.
    Your response must be under 75 words total.
    """
    
    response = run_llm(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model="llama-3.1-8b-instant"  # Using faster model for voice formatting
    )
    
    return response


def process_customer_query(user_query: str, conversation_history: Optional[List[ChatMessage]] = None) -> Tuple[str, List[ChatMessage]]:  # type: ignore
    """
    Process a customer query through the 3-step prompt chain.
    
    Args:
        user_query: The customer's question or request
        conversation_history: Optional list of previous messages
        
    Returns:
        Tuple containing:
            - Final response to the customer
            - Updated conversation history
    """
    # Initialize conversation history if None
    if conversation_history is None:
        conversation_history = []
    
    # Create a parent span for the entire prompt chain
    with tracer.start_as_current_span("prompt_chain") as parent_span:  # type: ignore
        # Add attributes to the parent span
        parent_span.set_attribute("user_query", user_query)
        parent_span.set_attribute("pattern", "prompt_chaining")
        
        # Step 1: Filter query for relevance
        with tracer.start_as_current_span("step1_filter_query_relevance") as span:
            span.set_attribute("step", "filter_query_relevance")
            is_relevant, explanation = step1_filter_query_relevance(user_query)
            span.set_attribute("is_relevant", is_relevant)
            span.set_attribute("explanation", explanation)
        
        if not is_relevant:
            response = f"I'm sorry, but I can only assist with questions related to KETL Mtn. Apparel products and services. {explanation}"
            # Add the interaction to conversation history
            conversation_history.append({"role": "user", "content": user_query})
            conversation_history.append({"role": "assistant", "content": response})
            parent_span.set_attribute("early_exit", True)
            return response, conversation_history
        
        # Step 2: Look up product information
        with tracer.start_as_current_span("step2_lookup_product_info") as span:
            span.set_attribute("step", "lookup_product_info")
            product_info = step2_lookup_product_info(user_query, conversation_history)
            span.set_attribute("product_info_length", len(product_info))
        
        # Step 3: Brand format response in brand voice
        with tracer.start_as_current_span("step3_brand_format_response") as span:
            span.set_attribute("step", "brand_format_response")
            final_response = step3_brand_format_response(product_info)
            span.set_attribute("response_length", len(final_response))
        
        # Add the interaction to conversation history
        conversation_history.append({"role": "user", "content": user_query})
        conversation_history.append({"role": "assistant", "content": final_response})
        
        # Add final attributes to parent span
        parent_span.set_attribute("completed", True)
        parent_span.set_attribute("steps_completed", 3)
        
        return final_response, conversation_history


def main():
    """Run an example of the prompt chaining workflow."""
    print("KETL Mtn. Apparel Customer Service Bot")
    print("-------------------------------------")
    print("Ask a question about our products or company (type 'exit' to quit):")
    
    # Initialize conversation history
    conversation_history: List[ChatMessage] = []
    
    while True:
        user_input = input("\nYour question: ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        response, conversation_history = process_customer_query(user_input, conversation_history)
        print("\nKETL Mtn. Response:")
        print(response)


if __name__ == "__main__":
    main()
