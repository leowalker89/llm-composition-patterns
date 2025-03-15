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
from pydantic import BaseModel, Field

# Define supported languages and their models
SUPPORTED_LANGUAGES = {
    "Spanish": "llama-3.3-70b-versatile",
    "French": "llama-3.3-70b-versatile",
    "German": "llama-3.3-70b-versatile",
    "Japanese": "qwen-2.5-32b",
    "Arabic": "mistral-saba-24b"
}


class ProductDetails(BaseModel):
    """Pydantic model for product details."""
    name: str
    features: str
    fabric: str
    other_details: str
    available_colors: List[str] = Field(default_factory=list)


class TranslatedProduct(BaseModel):
    """Pydantic model for translated product."""
    product_id: int
    original: ProductDetails
    translations: Dict[str, ProductDetails] = Field(default_factory=dict)


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


async def translate_product_details(product_details: ProductDetails, language: str, model: str) -> ProductDetails:
    """
    Translate all product details to the target language using a single LLM call.
    
    Args:
        product_details: ProductDetails object with original text
        language: Target language
        model: LLM model to use
        
    Returns:
        ProductDetails object with translated text
    """
    # Create a span for this specific translation
    with tracer.start_as_current_span(f"translate_to_{language}") as span:
        span.set_attribute("language", language)
        span.set_attribute("model", model)
        
        # Format colors as a comma-separated string for the prompt
        colors_str = ", ".join(product_details.available_colors)
        
        system_prompt = f"""
        You are a professional translator specializing in outdoor apparel terminology.
        Translate the provided product details from English to {language}.
        
        ONLY respond with valid JSON in this exact format:
        {{
            "name": "translated product name",
            "features": "translated product features",
            "fabric": "translated fabric details",
            "other_details": "translated other details",
            "available_colors": ["translated color 1", "translated color 2", ...]
        }}
        
        Maintain the same tone and style as the original text.
        """
        
        user_prompt = f"""
        Translate these product details to {language}:
        
        Product Name: {product_details.name}
        Product Features: {product_details.features}
        Fabric Details: {product_details.fabric}
        Other Details: {product_details.other_details}
        Available Colors: {colors_str}
        
        Return ONLY the JSON with the translated content.
        """
        
        try:
            response = await run_llm_async(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                model=model
            )
            
            # Parse the JSON response
            try:
                # Add a check to ensure response is not None before parsing
                if response is None:
                    span.set_attribute("success", False)
                    span.set_attribute("error", "Empty response from LLM")
                    print("Error: Empty response from LLM")
                    return ProductDetails(
                        name="Translation error (Empty response)",
                        features="Translation error (Empty response)",
                        fabric="Translation error (Empty response)",
                        other_details="Translation error (Empty response)",
                        available_colors=[]
                    )
                    
                json_response = json.loads(response)
                translated = ProductDetails(
                    name=json_response.get("name", "Translation error"),
                    features=json_response.get("features", "Translation error"),
                    fabric=json_response.get("fabric", "Translation error"),
                    other_details=json_response.get("other_details", "Translation error"),
                    available_colors=json_response.get("available_colors", [])
                )
                span.set_attribute("success", True)
                return translated
            except json.JSONDecodeError as e:
                span.set_attribute("success", False)
                span.set_attribute("error", f"JSON parse error: {str(e)}")
                print(f"Error parsing translation response: {e}")
                return ProductDetails(
                    name="Translation error (JSON parse failed)",
                    features="Translation error (JSON parse failed)",
                    fabric="Translation error (JSON parse failed)",
                    other_details="Translation error (JSON parse failed)",
                    available_colors=[]
                )
                
        except Exception as e:
            error_msg = str(e)
            span.set_attribute("success", False)
            span.set_attribute("error", error_msg)
            print(f"Translation error: {e}")
            return ProductDetails(
                name=f"Error: {error_msg}",
                features=f"Error: {error_msg}",
                fabric=f"Error: {error_msg}",
                other_details=f"Error: {error_msg}",
                available_colors=[]
            )


async def translate_product(product_id: int, languages: List[str], products: List[Dict]) -> TranslatedProduct:
    """
    Translate a product's details into multiple languages in parallel.
    
    Args:
        product_id: The product ID to translate
        languages: List of languages to translate to
        products: List of product dictionaries
        
    Returns:
        TranslatedProduct object with original and translations
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
            # Return an empty TranslatedProduct with an error message
            return TranslatedProduct(
                product_id=product_id,
                original=ProductDetails(
                    name=f"Product ID {product_id} not found", 
                    features="", 
                    fabric="",
                    other_details="",
                    available_colors=[]
                )
            )
        
        # Extract product details from the nested structure
        extracted_data = product.get("extracted_data", {})
        product_name = extracted_data.get("product_name", "Unknown Product")
        product_features = extracted_data.get("product_features", "")
        fabric_details = extracted_data.get("fabric_details", "")
        other_details = extracted_data.get("other_details", "")
        available_colors = extracted_data.get("available_colors", [])
        
        # Create original product details
        original_details = ProductDetails(
            name=product_name,
            features=product_features,
            fabric=fabric_details,
            other_details=other_details,
            available_colors=available_colors
        )
        
        parent_span.set_attribute("product_name", product_name)
        print(f"Translating product: {product_name}")
        
        # Create a TranslatedProduct object
        result = TranslatedProduct(
            product_id=product_id,
            original=original_details
        )
        
        # Create tasks for all translations (one per language)
        tasks = []
        for language in languages:
            if language not in SUPPORTED_LANGUAGES:
                continue
                
            model = SUPPORTED_LANGUAGES[language]
            tasks.append((language, translate_product_details(original_details, language, model)))
        
        # Await all translation tasks
        for language, task in tasks:
            try:
                translated_details = await task
                result.translations[language] = translated_details
            except Exception as e:
                print(f"Error processing translation to {language}: {e}")
                result.translations[language] = ProductDetails(
                    name="Translation error",
                    features="Translation error",
                    fabric="Translation error",
                    other_details="Translation error",
                    available_colors=[]
                )
        
        # Add final attributes to parent span
        parent_span.set_attribute("success", True)
        parent_span.set_attribute("languages_completed", len(result.translations))
        
        return result


def format_translation_result(result: TranslatedProduct) -> str:
    """
    Format translation result for display with English version for comparison.
    
    Args:
        result: TranslatedProduct object
        
    Returns:
        Formatted string for display
    """
    output = [f"Product ID: {result.product_id}", f"Original Name: {result.original.name}\n"]
    
    # Add English (original) section first
    output.append("=== English (Original) ===")
    output.append(f"Name: {result.original.name}")
    output.append(f"Features: {result.original.features}")
    output.append(f"Fabric: {result.original.fabric}")
    output.append(f"Other Details: {result.original.other_details}")
    output.append(f"Available Colors: {', '.join(result.original.available_colors)}")
    output.append("")  # Empty line between languages
    
    # Add translations for each language
    for language, translation in result.translations.items():
        output.append(f"=== {language} ===")
        output.append(f"Name: {translation.name}")
        output.append(f"Features: {translation.features}")
        output.append(f"Fabric: {translation.fabric}")
        output.append(f"Other Details: {translation.other_details}")
        output.append(f"Available Colors: {', '.join(translation.available_colors)}")
        output.append("")  # Empty line between languages
    
    return "\n".join(output)


def save_translations_to_json(result: TranslatedProduct, output_path: str) -> str:
    """
    Save the translated product details to a JSON file.
    
    Args:
        result: TranslatedProduct object
        output_path: Path to save the file
        
    Returns:
        Path to the saved file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Convert to dictionary for JSON serialization
    data = result.model_dump()
    
    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Translations saved to {output_path}")
    return output_path


async def main_async(product_id: int = 1, languages: Optional[List[str]] = None, output_path: Optional[str] = None):
    """
    Run an example of the parallelization pattern workflow.
    
    Args:
        product_id: ID of the product to translate
        languages: List of languages to translate to (defaults to Spanish, French, Japanese)
        output_path: Optional path to save the translations JSON file
    """
    # Default languages if none provided
    if languages is None:
        languages = ["Spanish", "French", "Japanese"]
    
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
        main_span.set_attribute("product_id", product_id)
        main_span.set_attribute("languages", ",".join(languages))
        
        print(f"Translating product ID {product_id} into {', '.join(languages)}...")
        print("This may take a moment as translations are processed in parallel...\n")
        
        # Translate the product
        result = await translate_product(product_id, languages, products)
        
        # Display the result
        print(format_translation_result(result))
        
        # Save the result to a JSON file if output_path is provided
        if output_path:
            saved_path = save_translations_to_json(result, output_path)
            if saved_path:
                main_span.set_attribute("output_file", saved_path)
        
        main_span.set_attribute("completed", True)


def main():
    """Entry point for the example."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Translate product details into multiple languages in parallel")
    parser.add_argument("--product-id", "-p", type=int, default=1, 
                        help="ID of the product to translate (default: 1)")
    parser.add_argument("--languages", "-l", type=str, nargs="+", 
                        choices=list(SUPPORTED_LANGUAGES.keys()),
                        default=["Spanish", "French", "Japanese"],
                        help="Languages to translate to (default: Spanish French Japanese)")
    parser.add_argument("--output", "-o", type=str, 
                        help="Path to save the translations JSON file")
    
    args = parser.parse_args()
    
    asyncio.run(main_async(args.product_id, args.languages, args.output))


if __name__ == "__main__":
    main()
