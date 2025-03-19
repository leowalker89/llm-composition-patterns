"""
Parallelization pattern implementation for translating product details.

This module demonstrates how to use asynchronous programming to parallelize
multiple LLM calls for translating product details into multiple languages.
"""

import os
import json
import asyncio
import time
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add these lines to enable tracing
from llm_composition_patterns.common.arize_phoenix_setup import enable_tracing_for_pattern
from opentelemetry import trace

# Enable tracing for this pattern
tracer_provider = enable_tracing_for_pattern("parallelization")
tracer = trace.get_tracer("parallelization")

# Now import the rest of the modules
from llm_composition_patterns.common.groq_helpers import run_llm_async
from llm_composition_patterns.common.ketlmtn_helpers import (
    load_products, 
    get_product_by_id
)
from llm_composition_patterns.common.models import ProductData
from pydantic import BaseModel, Field

# Language codes
LANGUAGE_CODES = {
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "japanese": "ja",
    "chinese": "zh"
}


class TranslatedProduct(BaseModel):
    """Pydantic model for translated product."""
    product_id: int
    original: ProductData
    translations: Dict[str, ProductData] = Field(default_factory=dict)


async def translate_product_details(product_data: ProductData, language: str, model: str) -> ProductData:
    """
    Translate all product details to the target language using a single LLM call.
    """
    with tracer.start_as_current_span(f"translate_to_{language}") as span:
        span.set_attribute("language", language)
        span.set_attribute("model", model)
        
        print(f"  🌐 Translating to {language}...")
        
        # Construct system prompt
        system_prompt = f"""
        You are a professional translator who specializes in translating product descriptions
        for e-commerce websites. You need to translate the following product details from
        English to {language}.
        
        Translate each of these product details, maintaining the original meaning and tone.
        Keep the technical details accurate.
        
        Return the translated content in JSON format with the following structure:
        {{
            "features": "Translated features",
            "fabric": "Translated fabric details",
            "other_details": "Translated other details",
            "available_colors": ["Color1", "Color2", ...]
        }}
        
        DO NOT translate the product name - we'll keep that in English.
        Return ONLY the JSON with the translations. Do not include any other text.
        """
        
        # Construct user prompt with product details
        user_prompt = f"""
        Please translate these product details to {language}:
        
        Product Name: {product_data.name} (DO NOT translate the name)
        
        Features: {product_data.features}
        
        Fabric Details: {product_data.fabric_details}
        
        Other Details: {product_data.details}
        
        Available Colors: {", ".join(product_data.colors)}
        """
        
        # Make the API call
        response = await run_llm_async(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            model=model
        )
        
        # Log the response length
        if response:
            span.set_attribute("response_length", len(response))
            
        # Parse the response for the translated content
        try:
            # Extract just the JSON content if we have a response
            if not response:
                raise ValueError("Empty response from LLM")
                
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_content = response[json_start:json_end]
            else:
                json_content = response
                
            # Parse the JSON
            translation_data = json.loads(json_content)
            
            # Create a new ProductData object with the translations
            # Keep the original name
            translated_product = ProductData(
                id=product_data.id,
                name=product_data.name,  # Keep original name
                features=translation_data.get("features", ""),
                fabric_details=translation_data.get("fabric", ""),
                details=translation_data.get("other_details", ""),
                colors=translation_data.get("available_colors", []),
                sizes=product_data.sizes,  # Keep original sizes
                price=product_data.price   # Keep original price
            )
            
            print(f"  ✅ Translated to {language}")
            span.set_attribute("success", True)
            return translated_product
            
        except Exception as e:
            print(f"  ⚠️ Error parsing {language} translation: {e}")
            span.set_attribute("success", False)
            span.set_attribute("error", str(e))
            
            # Return minimal translation with error flag
            return ProductData(
                id=product_data.id,
                name=product_data.name,  # Keep original name
                features=f"Error translating to {language}: {str(e)}",
                details="Translation failed",
                fabric_details="",
                colors=[]
            )


async def translate_product(product_id: int, languages: List[str], products: List[Dict]) -> TranslatedProduct:
    """
    Translate a product's details into multiple languages in parallel.
    
    Args:
        product_id: The product ID to translate
        languages: List of languages to translate to
        products: List of products from the database
        
    Returns:
        TranslatedProduct object with the original and all translations
    """
    with tracer.start_as_current_span(f"translate_product_{product_id}") as parent_span:
        parent_span.set_attribute("product_id", product_id)
        parent_span.set_attribute("languages", ",".join(languages))
        parent_span.set_attribute("num_languages", len(languages))
        
        # Find the product in the database
        product = get_product_by_id(product_id, products)
        
        if not product:
            print(f"Product ID {product_id} not found")
            return TranslatedProduct(
                product_id=product_id,
                original=ProductData(
                    id=product_id,
                    name=f"Product ID {product_id} not found",
                    features="Product not found",
                    details="No product data available"
                )
            )
        
        # Create original details from the product data
        original_details = ProductData(
            id=product["product_id"],
            name=product["extracted_data"]["product_name"],
            features=product["extracted_data"].get("product_features", ""),
            fabric_details=product["extracted_data"].get("fabric_details", ""),
            details=product["extracted_data"].get("other_details", ""),
            colors=product["extracted_data"].get("available_colors", []),
            sizes=product["extracted_data"].get("available_sizes", []),
            price=str(product["extracted_data"].get("price", ""))
        )
        
        # Initialize result object
        result = TranslatedProduct(
            product_id=product_id,
            original=original_details
        )
        
        # Define a helper function to translate to a specific language
        # This creates a cleaner closure for the async tasks
        async def translate_with_language(lang):
            translated = await translate_product_details(
                original_details, 
                lang,
                "llama-3.1-8b-instant"
            )
            return lang, translated
        
        # Create a list of tasks for parallel execution
        translation_tasks = [translate_with_language(lang) for lang in languages]
        
        # Execute all translation tasks in parallel
        start_time = time.time()
        translation_results = await asyncio.gather(*translation_tasks)
        end_time = time.time()
        
        # Calculate statistics
        total_time = end_time - start_time
        avg_time_per_lang = total_time / len(languages) if languages else 0
        
        # Add translations to the result
        for lang, translation in translation_results:
            result.translations[lang] = translation
        
        # Log performance metrics
        parent_span.set_attribute("total_translation_time_seconds", total_time)
        parent_span.set_attribute("average_time_per_language_seconds", avg_time_per_lang)
        
        return result


async def async_main(product_id: int = 1, 
                    languages: Optional[List[str]] = None, 
                    output_path: Optional[str] = None):
    """
    Main entry point for the parallelization pattern example.
    
    Args:
        product_id: ID of the product to translate (default: 1)
        languages: List of languages to translate to (default: Spanish, French, German)
        output_path: Optional path to save translation results
    """
    # Default languages if not specified
    if languages is None:
        languages = ["spanish", "french", "german"]
    
    print(f"Translating product ID {product_id} into {', '.join(languages)}...")
    
    # Load the product database
    print("Loading product data...")
    products = load_products()
    
    # Translate the product details
    print("Starting translation...")
    start = time.time()
    result = await translate_product(product_id, languages, products)
    end = time.time()
    
    # Display the results
    print("\n" + "="*60)
    print(f"Translation Results for {result.original.name}:")
    print("="*60)
    
    # Original product details
    print("\nOriginal (English):")
    print(f"Name: {result.original.name}")
    print(f"Features: {result.original.features[:80]}..." if len(result.original.features) > 80 else f"Features: {result.original.features}")
    print(f"Fabric: {result.original.fabric_details[:80]}..." if len(result.original.fabric_details) > 80 else f"Fabric: {result.original.fabric_details}")
    print(f"Other Details: {result.original.details[:80]}..." if len(result.original.details) > 80 else f"Other Details: {result.original.details}")
    print(f"Colors: {', '.join(result.original.colors)}")
    
    # Translations (one per language)
    for lang, translation in result.translations.items():
        print(f"\n{lang.capitalize()}:")
        print(f"  Name: {translation.name}")  # This will be the original English name
        print(f"  Features: {translation.features[:80]}..." if len(translation.features) > 80 else f"  Features: {translation.features}")
        print(f"  Fabric: {translation.fabric_details[:80]}..." if len(translation.fabric_details) > 80 else f"  Fabric: {translation.fabric_details}")
        print(f"  Other: {translation.details[:80]}..." if len(translation.details) > 80 else f"  Other: {translation.details}")
        print(f"  Colors: {', '.join(translation.colors)}")
    
    # Calculate and display performance stats
    total_time = end - start
    print("\n" + "="*50)
    print(f"Performance Statistics:")
    print(f"Total translation time: {total_time:.2f} seconds")
    print(f"Average time per language: {total_time/len(languages):.2f} seconds")
    print(f"Number of languages: {len(languages)}")
    print("="*50)
    
    # Save results to file if requested
    if output_path:
        result_data = result.model_dump()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_path}/translation_{product_id}_{timestamp}.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, "w") as f:
            json.dump(result_data, f, indent=2)
        print(f"\nResults saved to {filename}")
    
    return result


def main():
    """
    Command-line entry point for the parallelization pattern example.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Translate product details to multiple languages in parallel")
    parser.add_argument("--product", type=int, default=1, help="Product ID to translate")
    parser.add_argument("--languages", nargs="+", default=["spanish", "french", "german"],
                        help="Languages to translate to (default: spanish french german)")
    parser.add_argument("--output", type=str, help="Path to save translation results")
    
    args = parser.parse_args()
    
    asyncio.run(async_main(
        product_id=args.product,
        languages=args.languages,
        output_path=args.output
    ))


if __name__ == "__main__":
    main()
