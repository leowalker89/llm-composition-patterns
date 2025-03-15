"""
Example of routing pattern for KETL Mtn. Apparel customer service.

This module demonstrates a routing pattern:
1. Query classification to determine the appropriate handler
2. Routing to specialized handlers for different query types:
   - Product information queries
   - Company information queries
   - Warranty/guarantee queries
3. Response formatting according to brand voice
"""

import os
import json
from typing import Dict, List, Optional, Tuple, Union, Any, Literal
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add these lines to enable tracing - BEFORE importing any modules that use Groq
from llm_composition_patterns.common.arize_phoenix_setup import enable_tracing_for_pattern
from opentelemetry import trace  # type: ignore

# Enable tracing for this pattern - must be done before importing any modules that use Groq
tracer_provider = enable_tracing_for_pattern("routing")  # type: ignore
tracer = trace.get_tracer("routing")  # type: ignore

# Now import the rest of the modules that might use Groq
from llm_composition_patterns.common.groq_helpers import run_llm
from llm_composition_patterns.common.message_types import ChatMessage



# Define query types for routing
QueryType = Literal["product", "company", "warranty", "unclear"]


def load_product_data() -> List[Dict[str, Any]]:
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


def load_company_info() -> str:
    """
    Load company information from text file.
    
    Returns:
        String containing company information
    """
    info_path = Path(__file__).parent.parent.parent / "common" / "ketlmtn_data" / "about_us.txt"
    try:
        with open(info_path, "r") as f:
            return f.read()
    except FileNotFoundError as e:
        print(f"Error loading company info: {e}")
        return ""


def load_warranty_info() -> str:
    """
    Load warranty information from text file.
    
    Returns:
        String containing warranty information
    """
    warranty_path = Path(__file__).parent.parent.parent / "common" / "ketlmtn_data" / "lifetime_guarentee.txt"
    try:
        with open(warranty_path, "r") as f:
            return f.read()
    except FileNotFoundError as e:
        print(f"Error loading warranty info: {e}")
        return ""


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


def classify_query(user_query: str) -> Tuple[QueryType, float, str]:
    """
    Classify the query to determine which specialized handler should process it.
    
    Args:
        user_query: The customer's question or request
        
    Returns:
        Tuple containing:
            - Query type classification
            - Confidence score
            - Explanation of the classification
    """
    system_prompt = """
    You are a query classifier for KETL Mtn. Apparel, an outdoor gear company.
    Your task is to determine what type of information the customer is seeking.
    
    ONLY respond with valid JSON in this format:
    {
        "query_type": "product" | "company" | "warranty" | "unclear",
        "confidence": 0-100,
        "explanation": "Brief explanation of your classification"
    }
    
    Query types:
    - "product": Questions about specific products, features, pricing, availability, etc.
    - "company": Questions about KETL Mtn. as a company, its values, mission, sustainability, etc.
    - "warranty": Questions about product guarantees, repairs, returns, or the lifetime warranty
    - "unclear": Questions that don't clearly fit into the above categories or are ambiguous
    
    Be decisive in your classification. If a query could fit multiple categories, choose the most relevant one.
    If you truly cannot determine the category, classify as "unclear" and explain why it's unclear.
    For unclear queries, include in your explanation what clarification would be helpful.
    """
    
    user_prompt = f"Classify this customer query: '{user_query}'"
    
    response = run_llm(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model="llama-3.1-8b-instant"  # Using smaller model for classification
    )
    
    try:
        result = json.loads(response)
        return result["query_type"], result["confidence"], result["explanation"]
    except (json.JSONDecodeError, KeyError):
        # Fallback in case of parsing issues
        print(f"Warning: Failed to parse classifier response: {response}")
        return "unclear", 0.0, "I couldn't understand your question. Could you please clarify what you're asking about?"


def handle_product_query(user_query: str, conversation_history: Optional[List[ChatMessage]] = None) -> str:
    """
    Handle product-related queries by searching the product database.
    
    Args:
        user_query: The customer's question
        conversation_history: Optional list of previous messages
        
    Returns:
        String with detailed answer based on product information
    """
    system_prompt = """
    You are a product specialist for KETL Mtn. Apparel.
    Given a customer query and the product database, provide a detailed and accurate
    answer to their question based on the product information available.
    
    Be specific in your response, mentioning relevant product details,
    features, materials, and pricing when applicable.
    
    If the customer is referring to previous messages in the conversation,
    use that context to provide a more relevant answer.
    """
    
    # Load product data from JSON file
    product_data = load_product_data()
    
    # Convert product data to a string format that can be included in the prompt
    product_data_str = json.dumps(product_data, indent=2)
    
    user_prompt = f"""
    Customer query about KETL Mtn. products: '{user_query}'
    
    Product database:
    {product_data_str}
    
    Based on this information, provide a detailed answer to the customer's query.
    Reference the product catalog to ensure accuracy.
    """
    
    response = run_llm(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model="llama-3.3-70b-versatile",  # Using more capable model for product info
        message_history=conversation_history
    )
    
    return response


def handle_company_query(user_query: str, conversation_history: Optional[List[ChatMessage]] = None) -> str:
    """
    Handle company-related queries using the company information.
    
    Args:
        user_query: The customer's question
        conversation_history: Optional list of previous messages
        
    Returns:
        String with answer based on company information
    """
    system_prompt = """
    You are a company representative for KETL Mtn. Apparel.
    Given a customer query about the company and the company information,
    provide an accurate answer based on the available information.
    
    Be specific in your response, focusing on the company's values, mission,
    sustainability initiatives, and other relevant company details.
    
    If the customer is referring to previous messages in the conversation,
    use that context to provide a more relevant answer.
    """
    
    # Load company information
    company_info = load_company_info()
    
    user_prompt = f"""
    Customer query about KETL Mtn. as a company: '{user_query}'
    
    Company information:
    {company_info}
    
    Based on this information, provide a detailed answer to the customer's query.
    """
    
    response = run_llm(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model="llama-3.1-8b-instant",  # Using smaller model for company info
        message_history=conversation_history
    )
    
    return response


def handle_warranty_query(user_query: str, conversation_history: Optional[List[ChatMessage]] = None) -> str:
    """
    Handle warranty-related queries using the warranty information.
    
    Args:
        user_query: The customer's question
        conversation_history: Optional list of previous messages
        
    Returns:
        String with answer based on warranty information
    """
    system_prompt = """
    You are a customer service representative for KETL Mtn. Apparel.
    Given a customer query about warranties, guarantees, repairs, or returns,
    provide an accurate answer based on the available warranty information.
    
    Be specific in your response, focusing on the lifetime guarantee,
    repair process, and other relevant warranty details.
    
    If the customer is referring to previous messages in the conversation,
    use that context to provide a more relevant answer.
    """
    
    # Load warranty information
    warranty_info = load_warranty_info()
    
    user_prompt = f"""
    Customer query about KETL Mtn. warranty or repairs: '{user_query}'
    
    Warranty information:
    {warranty_info}
    
    Based on this information, provide a detailed answer to the customer's query.
    """
    
    response = run_llm(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model="llama-3.1-8b-instant",  # Using smaller model for warranty info
        message_history=conversation_history
    )
    
    return response


def format_response(raw_response: str) -> str:
    """
    Format the response according to KETL Mtn.'s brand voice.
    
    Args:
        raw_response: String with detailed answer
        
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
    - Include only the most essential details
    - Use casual, conversational language
    - Avoid lengthy explanations
    
    Rewrite the provided information in KETL Mtn.'s brand voice,
    but keep it extremely brief and to the point.
    """
    
    user_prompt = f"""
    Original information:
    {raw_response}
    
    Rewrite this in KETL Mtn.'s brand voice, making it EXTREMELY concise.
    Your response must be under 75 words total.
    """
    
    response = run_llm(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model="llama-3.1-8b-instant"  # Using faster model for voice formatting
    )
    
    return response


def process_customer_query(user_query: str, conversation_history: Optional[List[ChatMessage]] = None) -> Tuple[str, List[ChatMessage]]:
    """
    Process a customer query through the routing pattern.
    
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
    
    # Create a parent span for the entire routing process
    with tracer.start_as_current_span("routing_pattern") as parent_span:
        parent_span.set_attribute("user_query", user_query)
        parent_span.set_attribute("pattern", "routing")
        
        # Step 1: Classify the query
        with tracer.start_as_current_span("step1_classify_query") as span:
            span.set_attribute("step", "classify_query")
            query_type, confidence, explanation = classify_query(user_query)
            span.set_attribute("query_type", query_type)
            span.set_attribute("confidence", confidence)
            span.set_attribute("explanation", explanation)
        
        # Step 2: Route to the appropriate handler
        with tracer.start_as_current_span("step2_handle_query") as span:
            span.set_attribute("step", "handle_query")
            span.set_attribute("handler", query_type)
            
            if query_type == "product":
                raw_response = handle_product_query(user_query, conversation_history)
            elif query_type == "company":
                raw_response = handle_company_query(user_query, conversation_history)
            elif query_type == "warranty":
                raw_response = handle_warranty_query(user_query, conversation_history)
            else:  # "unclear"
                # For unclear queries, use the explanation from the classifier
                # and add a request for clarification
                raw_response = f"{explanation} Could you please clarify if you're asking about our products, our company, or our warranty/repair process?"
            
            span.set_attribute("response_length", len(raw_response))
        
        # Step 3: Format the response in brand voice (for all responses)
        with tracer.start_as_current_span("step3_format_response") as span:
            span.set_attribute("step", "format_response")
            final_response = format_response(raw_response)
            span.set_attribute("response_length", len(final_response))
        
        # Add the interaction to conversation history
        conversation_history.append({"role": "user", "content": user_query})
        conversation_history.append({"role": "assistant", "content": final_response})
        
        # Add final attributes to parent span
        parent_span.set_attribute("completed", True)
        parent_span.set_attribute("steps_completed", 3)
        
        return final_response, conversation_history


def main() -> None:
    """Run an example of the routing pattern workflow."""
    print("KETL Mtn. Apparel Customer Service Bot (Routing Pattern)")
    print("-----------------------------------------------------")
    print("Ask a question about our products, company, or warranty (type 'exit' to quit):")
    
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
