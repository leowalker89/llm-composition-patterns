"""
Example of parallelization pattern for KETL Mtn. Apparel product translations.

This module demonstrates a parallelization pattern:
1. Takes a list of product IDs and target languages
2. Translates product details into multiple languages in parallel
3. Returns the translated product information
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, cast
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add these lines to enable tracing - BEFORE importing any modules that use Groq
from llm_composition_patterns.common.arize_phoenix_setup import enable_tracing_for_pattern
from opentelemetry import trace  # type: ignore

# Enable tracing for this pattern - must be done before importing any modules that use Groq
tracer_provider = enable_tracing_for_pattern("parallelization")  # type: ignore
tracer = trace.get_tracer("parallelization")  # type: ignore

# Now import the rest of the modules that might use Groq
from llm_composition_patterns.common.groq_helpers import run_llm_async

# Define supported languages and their models
SUPPORTED_LANGUAGES = {
    "Spanish": "llama-3.3-70b-versatile",
    "French": "llama-3.3-70b-versatile",
    "German": "llama-3.3-70b-versatile",
    "Japanese": "qwen-2.5-32b",
    "Arabic": "mistral-saba-24b"
}


def load_products() -> List[Dict]:
    """
    Load product data from JSON file.
    
    Returns:
        List of product dictionaries
    """
    json_path = Path(__file__).parent.parent.parent / "common" / "ketlmtn_data" / "ketlmtn_products.json"
    try:
        with open(json_path, "r") as f:
            products = json.load(f)
            print(f"Loaded {len(products)} products")
            return products
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading product data: {e}")
        return []


def get_product_by_id(product_id: int, products: List[Dict]) -> Optional[Dict]:
    """
    Get a product by its ID.
    
    Args:
        product_id: The product ID to find
        products: List of product dictionaries
        
    Returns:
        Product dictionary or None if not found
    """
    for product in products:
        if product.get("product_id") == product_id:
            return product
    return None


async def translate_text(text: str, language: str, model: str) -> str:
    """
    Translate text to the target language using the specified model.
    
    Args:
        text: Text to translate
        language: Target language
        model: LLM model to use
        
    Returns:
        Translated text
    """
    # Create a span for this specific translation
    with tracer.start_as_current_span(f"translate_to_{language}") as span:
        span.set_attribute("language", language)
        span.set_attribute("model", model)
        span.set_attribute("text_length", len(text))
        
        system_prompt = f"""
        You are a professional translator specializing in outdoor apparel terminology.
        Translate the provided text into {language}.
        
        ONLY respond with the translated text, nothing else.
        """
        
        user_prompt = f"Translate this text to {language}: {text}"
        
        try:
            response = await run_llm_async(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                model=model
            )
            result = response.strip() if response else ""
            span.set_attribute("success", True)
            span.set_attribute("result_length", len(result))
            return result
        except Exception as e:
            error_msg = str(e)
            span.set_attribute("success", False)
            span.set_attribute("error", error_msg)
            print(f"Translation error: {e}")
            return f"Error: {error_msg}"


async def translate_product(product_id: int, languages: List[str], products: List[Dict]) -> Dict[str, Any]:
    """
    Translate a product's details into multiple languages in parallel.
    
    Args:
        product_id: The product ID to translate
        languages: List of languages to translate to
        products: List of product dictionaries
        
    Returns:
        Dictionary with original product and translations
    """
    # Create a parent span for the entire product translation process
    with tracer.start_as_current_span("translate_product") as parent_span:
        parent_span.set_attribute("product_id", product_id)
        parent_span.set_attribute("languages", ",".join(languages))
        parent_span.set_attribute("pattern", "parallelization")
        
        # Get the product
        product = get_product_by_id(product_id, products)
        if not product:
            parent_span.set_attribute("error", f"Product ID {product_id} not found")
            parent_span.set_attribute("success", False)
            return {"error": f"Product ID {product_id} not found"}
        
        # Extract product details from the nested structure
        extracted_data = product.get("extracted_data", {})
        product_name = extracted_data.get("product_name", "Unknown Product")
        product_features = extracted_data.get("product_features", "")
        fabric_details = extracted_data.get("fabric_details", "")
        
        parent_span.set_attribute("product_name", product_name)
        print(f"Translating product: {product_name}")
        
        # Create tasks for all translations
        tasks = []
        for language in languages:
            if language not in SUPPORTED_LANGUAGES:
                continue
                
            model = SUPPORTED_LANGUAGES[language]
            
            # Create translation tasks for each field
            name_task = translate_text(product_name, language, model)
            features_task = translate_text(product_features, language, model)
            fabric_task = translate_text(fabric_details, language, model)
            
            tasks.append((language, "name", name_task))
            tasks.append((language, "features", features_task))
            tasks.append((language, "fabric", fabric_task))
        
        # Execute all translations in parallel
        result: Dict[str, Any] = {
            "product_id": product_id,
            "original": {
                "name": product_name,
                "features": product_features,
                "fabric": fabric_details
            },
            "translations": {}
        }
        
        # Initialize translation structure
        for language in languages:
            if language in SUPPORTED_LANGUAGES:
                translations_dict = cast(Dict[str, Dict[str, str]], result["translations"])
                translations_dict[language] = {}
        
        # Await all translation tasks
        for language, field, task in tasks:
            try:
                translated_text = await task
                translations_dict = cast(Dict[str, Dict[str, str]], result["translations"])
                translations_dict[language][field] = translated_text
            except Exception as e:
                print(f"Error processing {field} translation to {language}: {e}")
                translations_dict = cast(Dict[str, Dict[str, str]], result["translations"])
                translations_dict[language][field] = "Translation error"
        
        # Add final attributes to parent span
        parent_span.set_attribute("success", True)
        parent_span.set_attribute("languages_completed", len(result["translations"]))
        parent_span.set_attribute("fields_per_language", 3)  # name, features, fabric
        
        return result


def format_translation_result(result: Dict) -> str:
    """
    Format translation result for display with English version for comparison.
    
    Args:
        result: Translation result dictionary
        
    Returns:
        Formatted string for display
    """
    if "error" in result:
        return f"Error: {result['error']}"
    
    output = [f"Product ID: {result['product_id']}", f"Original Name: {result['original']['name']}\n"]
    
    # Add English (original) section first
    output.append("=== English (Original) ===")
    output.append(f"Name: {result['original']['name']}")
    output.append(f"Features: {result['original']['features']}")
    output.append(f"Fabric: {result['original']['fabric']}")
    output.append("")  # Empty line between languages
    
    # Add translations for each language
    for language, translations in result["translations"].items():
        output.append(f"=== {language} ===")
        for field, text in translations.items():
            # Show original English text alongside the translation for comparison
            original_text = result['original'][field]
            output.append(f"{field.capitalize()}: {text}")
            output.append(f"  Original: {original_text}")
            output.append("")  # Add space between fields for readability
        output.append("")  # Empty line between languages
    
    return "\n".join(output)


async def main_async():
    """Run an example of the parallelization pattern workflow."""
    # Create a span for the entire example
    with tracer.start_as_current_span("parallelization_example") as main_span:
        print("KETL Mtn. Apparel Product Translator (Parallelization Pattern)")
        print("-----------------------------------------------------------")
        
        # Load all products
        products = load_products()
        if not products:
            main_span.set_attribute("error", "No products found")
            print("No products found. Please check the JSON file path.")
            return
        
        main_span.set_attribute("products_loaded", len(products))
        
        # Example: Translate product ID 1 to multiple languages
        product_id = 1
        languages = ["Spanish", "French", "Japanese"]  # Using fewer languages for a quicker demo
        
        main_span.set_attribute("product_id", product_id)
        main_span.set_attribute("languages", ",".join(languages))
        
        print(f"Translating product ID {product_id} into {', '.join(languages)}...")
        print("This may take a moment as translations are processed in parallel...\n")
        
        # Translate the product
        result = await translate_product(product_id, languages, products)
        
        # Display the result
        print(format_translation_result(result))
        
        main_span.set_attribute("completed", True)


def main():
    """Entry point for the example."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
