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


async def translate_product_details(product_details: ProductDetails, language: str, model: str) -> ProductDetails:
    """
    Translate all product details to the target language using a single LLM call.
    """
    with tracer.start_as_current_span(f"translate_to_{language}") as span:
        span.set_attribute("language", language)
        span.set_attribute("model", model)
        
        # Format colors as a comma-separated string for the prompt
        colors_str = ", ".join(product_details.available_colors)
        
        # Get schema for prompt
        schema_example = json.dumps(ProductDetails.model_json_schema(), indent=2)
        
        system_prompt = f"""
        You are a professional translator specializing in outdoor apparel terminology.
        Translate the provided product details from English to {language}.
        
        ONLY respond with valid JSON matching the Pydantic model schema:
        {schema_example}
        
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
            
            # Simple empty response check
            if not response:
                return ProductDetails(
                    name="Translation error", 
                    features="Empty response from LLM",
                    fabric="", other_details="",
                    available_colors=[]
                )
            
            # Let Pydantic handle validation directly
            return ProductDetails.model_validate_json(response)
            
        except Exception as e:
            # Simplified error handling - just create the error instance directly 
            return ProductDetails(
                name="Translation error", 
                features=str(e),
                fabric="", other_details="",
                available_colors=[]
            )


async def translate_product(product_id: int, languages: List[str], products: List[Dict]) -> TranslatedProduct:
    """
    Translate a product's details into multiple languages in parallel.
    
    This function demonstrates the parallelization pattern by:
    1. Taking a product ID and list of target languages
    2. Running multiple translations concurrently using asyncio.gather
    3. Returning all translations as a single object
    
    Args:
        product_id: The product ID to translate
        languages: List of languages to translate to
        products: List of product dictionaries
        
    Returns:
        TranslatedProduct object with original and translations
    """
    with tracer.start_as_current_span("translate_product") as parent_span:
        parent_span.set_attribute("product_id", product_id)
        parent_span.set_attribute("languages", ",".join(languages))
        parent_span.set_attribute("pattern", "parallelization")
        
        # Find the product directly - no need for a separate function
        product = next((p for p in products if p.get("product_id") == product_id), None)
        
        if not product:
            return TranslatedProduct(
                product_id=product_id,
                original=ProductDetails(
                    name=f"Product ID {product_id} not found",
                    features="", fabric="", other_details="",
                    available_colors=[]
                )
            )
        
        # Create original details from the product data
        extracted_data = product.get("extracted_data", {})
        original_details = ProductDetails(
            name=extracted_data.get("product_name", "Unknown Product"),
            features=extracted_data.get("product_features", ""),
            fabric=extracted_data.get("fabric_details", ""),
            other_details=extracted_data.get("other_details", ""),
            available_colors=extracted_data.get("available_colors", [])
        )
        
        # Create result object
        result = TranslatedProduct(
            product_id=product_id,
            original=original_details
        )
        
        # Filter to supported languages only
        supported_languages = [lang for lang in languages if lang in SUPPORTED_LANGUAGES]
        
        # Run translations in parallel
        async def translate_with_language(lang):
            try:
                model = SUPPORTED_LANGUAGES[lang]
                translated = await translate_product_details(original_details, lang, model)
                return lang, translated
            except Exception as e:
                print(f"Error translating to {lang}: {e}")
                return lang, ProductDetails(
                    name="Translation error", 
                    features=str(e),
                    fabric="", other_details="",
                    available_colors=[]
                )
        
        # This is the key parallelization pattern
        translation_results = await asyncio.gather(
            *(translate_with_language(lang) for lang in supported_languages)
        )
        
        # Store results
        for lang, translation in translation_results:
            result.translations[lang] = translation
            
        return result


async def async_main(product_id: int = 1, 
                    languages: Optional[List[str]] = None, 
                    output_path: Optional[str] = None):
    """
    Async entry point for the parallelization pattern example.
    
    Args:
        product_id: ID of the product to translate (default: 1)
        languages: Languages to translate to (default: Spanish, French, Japanese)
        output_path: Optional path to save results to a JSON file
    """
    # Set default languages if none provided
    if languages is None:
        languages = ["Spanish", "French", "Japanese"]
    
    print(f"Translating product ID {product_id} into {', '.join(languages)}...")
    
    # Load products
    products = load_products()
    if not products:
        print("No products found. Please check the JSON file path.")
        return None
    
    # This is where the parallelization happens
    print("Running translations in parallel...")
    result = await translate_product(product_id, languages, products)
    
    # Display results
    print(f"\nProduct: {result.original.name}")
    for lang, translation in result.translations.items():
        print(f"{lang}: {translation.name}")
    
    # Save if requested
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))
        print(f"Saved full results to {output_path}")
    
    return result


def main():
    """Entry point for the example from command line."""
    # Simply call the async function with default parameters
    return asyncio.run(async_main())


if __name__ == "__main__":
    main()
