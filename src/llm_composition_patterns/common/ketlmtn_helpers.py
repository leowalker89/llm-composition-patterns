"""
Helper functions for KETL Mountain Apparel examples.

This module provides centralized data loading and processing functions
used across different LLM composition pattern examples.
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import os


def get_data_file_path(filename: str) -> Path:
    """
    Get the full path to a data file in the ketlmtn_data directory.
    
    Args:
        filename: Name of the file to locate
        
    Returns:
        Path object to the requested file
    """
    base_path = Path(__file__).parent / "ketlmtn_data"
    return base_path / filename


def load_products() -> List[Dict]:
    """
    Load product data from JSON file.
    
    Returns:
        List of product dictionaries
    """
    json_path = get_data_file_path("ketlmtn_products.json")
    try:
        with open(json_path, "r") as f:
            products = json.load(f)
            print(f"Loaded {len(products)} products")
            return products
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading product data: {e}")
        return []


def load_brand_voice() -> Dict[str, Any]:
    """
    Load brand voice guidelines from JSON file.
    
    Returns:
        Dictionary containing brand voice information
    """
    json_path = get_data_file_path("ketlmtn_brand_voice.json")
    try:
        with open(json_path, "r") as f:
            brand_voice = json.load(f)
            return brand_voice
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading brand voice data: {e}")
        return {}


def get_product_by_id(product_id: int, products: List[Dict]) -> Optional[Dict]:
    """
    Get a product by its ID.
    
    Args:
        product_id: The product ID to find
        products: List of product dictionaries
        
    Returns:
        Product dictionary or None if not found
    """
    return next((p for p in products if p.get("product_id") == product_id), None)


def load_company_info() -> str:
    """
    Load company information from text file.
    
    Returns:
        String containing company information
    """
    info_path = get_data_file_path("about_us.txt")
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
    warranty_path = get_data_file_path("lifetime_guarentee.txt")
    try:
        with open(warranty_path, "r") as f:
            return f.read()
    except FileNotFoundError as e:
        print(f"Error loading warranty info: {e}")
        return ""


def load_brand_voice_text() -> str:
    """
    Load brand voice guidelines from text file.
    
    Returns:
        String containing brand voice guidelines
    """
    voice_path = get_data_file_path("brand_voice.txt")
    try:
        with open(voice_path, "r") as f:
            return f.read()
    except FileNotFoundError as e:
        print(f"Error loading brand voice: {e}")
        return ""


def load_sales_pitches() -> List[Dict]:
    """Load KETL Mtn. sales pitch data."""
    file_path = os.path.join(os.path.dirname(__file__), "ketlmtn_data/ketlmtn_sales_pitch.json")
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading sales pitches: {e}")
        return []


def get_sales_pitch_by_id(product_id: int, pitches: Optional[List[Dict]] = None) -> Optional[Dict]:
    """
    Get a sales pitch by product ID.
    
    Args:
        product_id: The product ID to find
        pitches: Optional list of pitch dictionaries (loaded if not provided)
        
    Returns:
        Sales pitch dictionary or None if not found
    """
    if pitches is None:
        pitches = load_sales_pitches()
        
    return next((p for p in pitches if p.get("product_id") == product_id), None)


def get_original_pitch(product_id: int) -> Optional[str]:
    """
    Get the original sales pitch text for a product ID.
    
    Args:
        product_id: The product ID to find
        
    Returns:
        Original sales pitch text or None if not found
    """
    pitch_data = get_sales_pitch_by_id(product_id)
    if pitch_data:
        return pitch_data.get("sales_pitch")
    return None


def get_example_pitches(limit: int = 3, exclude_id: Optional[int] = None) -> List[Dict]:
    """
    Get a limited set of sales pitches to use as examples.
    
    Args:
        limit: Maximum number of example pitches to return
        exclude_id: Optional product ID to exclude from examples
        
    Returns:
        List of example pitch dictionaries
    """
    pitches = load_sales_pitches()
    
    # Filter out the excluded product if specified
    if exclude_id is not None:
        filtered_pitches = [p for p in pitches if p.get("product_id") != exclude_id]
    else:
        filtered_pitches = pitches
    
    # Return a subset of pitches as examples
    return filtered_pitches[:limit]


def load_product_data(product_id: int) -> Any:  # Return type is Any to avoid circular imports
    """Load product data as a structured object."""
    # Try main database first
    product = get_product_by_id(product_id, load_products())
    if product:
        return product
        
    # Try sales pitch database next
    pitch = get_sales_pitch_by_id(product_id)
    if pitch:
        return {
            "product_id": pitch["product_id"],
            "extracted_data": {
                "product_name": pitch["product_name"],
                "other_details": "An outdoor product from KETL Mtn. Apparel."
            }
        }
    
    # Minimal fallback
    return {
        "product_id": product_id,
        "extracted_data": {
            "product_name": f"Product {product_id}",
            "other_details": "An outdoor product from KETL Mtn. Apparel."
        }
    }


# Add other helper functions as needed
