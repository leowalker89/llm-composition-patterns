"""
Evaluator-Optimizer pattern implementation for KETL Mtn. sales pitch generation.

This module demonstrates how to use the evaluator-optimizer pattern to generate
and iteratively refine sales pitches for KETL Mtn. products based on brand voice
guidelines and effectiveness criteria.
"""

import json
import os
import asyncio
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import sys

# Fix the import path by adding the src directory to sys.path
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import helpers
from llm_composition_patterns.common.groq_helpers import run_llm_async

# Load environment variables
load_dotenv()

# Define types for iteration tracking
@dataclass
class IterationData:
    """Data for tracking an iteration of the optimization process."""
    pitch: str
    evaluation: Optional[Dict[str, Any]] = None
    feedback: Optional[str] = None

def load_product_data(product_id: int) -> Dict:
    """
    Load specific product data by ID from the KETL Mtn. product database.
    
    Args:
        product_id: The ID of the product to load
        
    Returns:
        Product data dictionary
    """
    data_dir = Path(__file__).parent.parent.parent / "common" / "ketlmtn_data"
    
    # Load products
    with open(data_dir / "ketlmtn_products.json") as f:
        products = json.load(f)
    
    print(f"🔍 Looking for product ID {product_id} in database with {len(products)} products")
    
    # Check the first product to see its structure
    if products and len(products) > 0:
        first_product = products[0]
        print(f"📋 Sample product structure: {list(first_product.keys())}")
    
    # Find the product with the matching ID
    for product in products:
        if product.get("product_id") == product_id:
            # Create a flattened version of the product data for easier use
            flattened_product = {
                "id": product["product_id"],
                "name": product["extracted_data"]["product_name"],
                "features": product["extracted_data"].get("product_features", ""),
                "fabric_details": product["extracted_data"].get("fabric_details", ""),
                "other_details": product["extracted_data"].get("other_details", ""),
                "price": product["extracted_data"].get("price", ""),
                "colors": product["extracted_data"].get("available_colors", []),
                "sizes": product["extracted_data"].get("available_sizes", []),
                "inseams": product["extracted_data"].get("available_inseams", [])
            }
            return flattened_product
    
    raise ValueError(f"Product with ID {product_id} not found")

def load_brand_voice() -> str:
    """
    Load KETL Mtn. brand voice guidelines.
    
    Returns:
        Brand voice guidelines as a string
    """
    data_dir = Path(__file__).parent.parent.parent / "common" / "ketlmtn_data"
    
    with open(data_dir / "brand_voice.txt") as f:
        brand_voice = f.read()
    
    return brand_voice

def load_original_pitch(product_id: int) -> Optional[str]:
    """
    Load the original sales pitch for a product if it exists.
    
    Args:
        product_id: The ID of the product
        
    Returns:
        Original sales pitch or None if not found
    """
    data_dir = Path(__file__).parent.parent.parent / "common" / "ketlmtn_data"
    
    with open(data_dir / "ketlmtn_sales_pitch.json") as f:
        sales_pitches = json.load(f)
    
    for pitch_data in sales_pitches:
        if pitch_data.get("product_id") == product_id:
            return pitch_data.get("sales_pitch")
    
    return None

def load_example_pitches(limit: int = 3, exclude_id: Optional[int] = None) -> List[Dict]:
    """
    Load high-performing example pitches for reference.
    
    Args:
        limit: Maximum number of example pitches to load
        exclude_id: Optional product ID to exclude from examples
        
    Returns:
        List of example pitch dictionaries
    """
    data_dir = Path(__file__).parent.parent.parent / "common" / "ketlmtn_data"
    
    with open(data_dir / "ketlmtn_sales_pitch.json") as f:
        all_pitches = json.load(f)
    
    # Filter out the excluded product if specified
    if exclude_id is not None:
        filtered_pitches = [p for p in all_pitches if p.get("product_id") != exclude_id]
    else:
        filtered_pitches = all_pitches
    
    # Return a subset of pitches as examples
    return filtered_pitches[:limit]

def extract_json_from_response(response: str) -> str:
    """Extract JSON from a response that might contain markdown formatting."""
    # Check if response contains a JSON code block
    if "```json" in response:
        # Extract content between ```json and ```
        start = response.find("```json") + 7
        end = response.find("```", start)
        if end > start:
            return response[start:end].strip()
    
    # Check if response contains any code block
    if "```" in response:
        # Extract content between ``` and ```
        start = response.find("```") + 3
        end = response.find("```", start)
        if end > start:
            return response[start:end].strip()
    
    # Return the original response if no code blocks found
    return response

async def generate_sales_pitch(
    product_data: Dict, 
    brand_voice: str,
    previous_attempts: Optional[List[str]] = None,
    feedback: Optional[str] = None,
    original_pitch: Optional[str] = None
) -> str:
    """
    Generate a sales pitch for a KETL Mtn. product.
    
    Args:
        product_data: Product specifications
        brand_voice: KETL brand voice guidelines
        previous_attempts: Optional list of prior pitches
        feedback: Optional feedback from evaluator
        original_pitch: Optional original sales pitch for reference
        
    Returns:
        Generated sales pitch text
    """
    print(f"\n🖋️ GENERATOR: Creating sales pitch for {product_data.get('name', 'product')}...")
    
    # Load example pitches for reference
    example_pitches = load_example_pitches(limit=2, exclude_id=product_data.get("id"))
    example_text = ""
    if example_pitches:
        example_text = "Here are examples of successful KETL Mtn. sales pitches:\n\n"
        for i, example in enumerate(example_pitches):
            example_text += f"Example {i+1} - {example.get('product_name')}:\n{example.get('sales_pitch')}\n\n"
    
    # Include original pitch if available
    original_pitch_text = ""
    if original_pitch:
        original_pitch_text = f"""
        Original pitch for this product (use as reference but create a new, improved version):
        {original_pitch}
        """
    
    # Construct feedback incorporation instructions if available
    feedback_instructions = ""
    if previous_attempts and feedback:
        feedback_instructions = f"""
        Previous attempt:
        {previous_attempts[-1]}
        
        Feedback on previous attempt:
        {feedback}
        
        Please address this feedback in your new version while maintaining KETL's brand voice.
        """
    
    # Add creative instructions if we have minimal product data
    creative_instructions = ""
    if len(product_data.keys()) <= 3:  # Only has id, name, and maybe description
        creative_instructions = """
        Note: You have minimal product data to work with. Use your creativity to imagine 
        what this KETL Mtn. product might be like based on its name and the brand voice.
        Focus on creating an engaging pitch that captures the spirit of KETL Mtn. products.
        """
    
    # Construct system prompt
    system_prompt = f"""
    You are an expert copywriter for KETL Mtn. Apparel, creating compelling sales pitches for outdoor gear.

    Product information:
    {json.dumps(product_data, indent=2)}

    Brand voice guidelines:
    {brand_voice}

    {example_text}
    
    {original_pitch_text}
    
    {creative_instructions}

    Your task is to write an engaging sales pitch for this product that:
    1. Highlights key features and benefits
    2. Uses authentic, conversational language
    3. Mentions the lifetime repair guarantee
    4. Includes a call to action about free shipping/returns
    5. Maintains KETL's casual, enthusiastic tone
    6. Is concise - approximately 30 seconds when read aloud (about 75-100 words)

    Keep the pitch focused on the most important selling points. Be concise while maintaining the conversational, enthusiastic tone that defines KETL's brand voice.

    {feedback_instructions}

    Format your response with:
    Thoughts: [Brief analysis of the product and approach]
    Sales Pitch: [Your complete sales pitch]
    """
    
    # Generate the pitch
    response = await run_llm_async(
        user_prompt="Generate a compelling, concise sales pitch for this KETL Mtn. product.",
        system_prompt=system_prompt,
        model="llama-3.1-8b-instant"
    )
    
    if not response:
        raise Exception("Failed to generate sales pitch")
    
    # Extract just the sales pitch part
    if "Sales Pitch:" in response:
        pitch = response.split("Sales Pitch:")[1].strip()
    else:
        pitch = response
    
    print(f"✅ Generated pitch ({len(pitch)} chars, ~{len(pitch.split())} words)")
    return pitch

async def evaluate_sales_pitch(pitch: str, product_data: Dict, brand_voice: str) -> Dict[str, Any]:
    """
    Evaluate a sales pitch against KETL brand guidelines and effectiveness criteria.
    
    Args:
        pitch: The sales pitch to evaluate
        product_data: Original product information
        brand_voice: KETL brand voice guidelines
        
    Returns:
        Evaluation results with pass/fail status and detailed feedback
    """
    print(f"\n🔍 EVALUATOR: Analyzing sales pitch...")
    
    # Construct system prompt for evaluation
    system_prompt = f"""
    You are a quality assurance specialist for KETL Mtn. Apparel, evaluating sales pitches.

    Your task is to critically analyze the submitted sales pitch against our brand guidelines and effectiveness criteria.

    Brand voice guidelines:
    {brand_voice}

    Product information:
    {json.dumps(product_data, indent=2)}

    Sales pitch to evaluate:
    {pitch}

    Evaluate the following criteria and provide specific feedback:
    1. Brand Voice: Is the tone authentic, conversational, and aligned with KETL's voice?
    2. Feature Completeness: Does it cover key product features and benefits?
    3. Technical Accuracy: Are all claims factually correct based on product data?
    4. Persuasiveness: Is the pitch compelling and likely to drive action?
    5. Policy Mention: Does it include our lifetime repair guarantee and free shipping/returns?
    6. Conciseness: Is the pitch concise enough to be spoken in about 30 seconds (75-100 words)?

    Return a JSON object with:
    {{
      "status": "PASS" or "NEEDS_IMPROVEMENT",
      "criteria": {{
        "brand_voice": "PASS" or "FAIL",
        "feature_completeness": "PASS" or "FAIL",
        "technical_accuracy": "PASS" or "FAIL",
        "persuasiveness": "PASS" or "FAIL",
        "policy_mention": "PASS" or "FAIL",
        "conciseness": "PASS" or "FAIL"
      }},
      "feedback": "Detailed feedback explaining issues and suggesting improvements",
      "word_count": [approximate word count of the pitch]
    }}

    Only return "PASS" for the overall status if ALL criteria are marked as "PASS".
    """
    
    # Generate the evaluation
    response = await run_llm_async(
        user_prompt="Evaluate this sales pitch against our criteria.",
        system_prompt=system_prompt,
        model="llama-3.1-8b-instant"
    )
    
    if not response:
        raise Exception("Failed to evaluate sales pitch")
    
    # Extract JSON from the response
    try:
        # Handle potential markdown formatting
        json_str = extract_json_from_response(response)
        evaluation = json.loads(json_str)
        
        # Print evaluation summary
        print(f"📊 Evaluation results:")
        for criterion, result in evaluation["criteria"].items():
            print(f"  {criterion}: {result}")
        if "word_count" in evaluation:
            print(f"  Word count: {evaluation['word_count']} words")
        print(f"📋 Overall status: {evaluation['status']}")
        
        return evaluation
    except json.JSONDecodeError as e:
        print(f"⚠️ Error parsing evaluation JSON: {e}")
        print(f"Raw response: {response}")
        
        # Return a default evaluation
        return {
            "status": "NEEDS_IMPROVEMENT",
            "criteria": {
                "brand_voice": "FAIL",
                "feature_completeness": "FAIL",
                "technical_accuracy": "FAIL",
                "persuasiveness": "FAIL",
                "policy_mention": "FAIL",
                "conciseness": "FAIL"
            },
            "feedback": "Unable to parse evaluation. Please improve the pitch focusing on brand voice, feature completeness, technical accuracy, persuasiveness, policy mentions, and conciseness.",
            "word_count": len(pitch.split())
        }

async def optimize_sales_pitch(product_id: int, max_iterations: int = 3) -> Tuple[str, List[IterationData]]:
    """
    Create an optimized sales pitch through iterative refinement.
    
    Args:
        product_id: ID of the product to create a pitch for
        max_iterations: Maximum number of refinement iterations
        
    Returns:
        Tuple of (final_pitch, iteration_history)
    """
    print(f"\n🚀 Starting evaluator-optimizer workflow for product ID {product_id}...")
    
    # Load necessary data
    product_data = None
    
    # First try loading from product database
    try:
        product_data = load_product_data(product_id)
        print(f"✅ Loaded product data: {product_data.get('name', 'Unknown product')}")
        print(f"📋 Product fields: {list(product_data.keys())}")
    except ValueError as e:
        print(f"⚠️ Product ID {product_id} not found in main product database: {e}")
    
    # If not found in product database, try loading from sales pitch data
    if product_data is None:
        try:
            data_dir = Path(__file__).parent.parent.parent / "common" / "ketlmtn_data"
            with open(data_dir / "ketlmtn_sales_pitch.json") as f:
                sales_pitches = json.load(f)
            
            for pitch_data in sales_pitches:
                if pitch_data.get("product_id") == product_id:
                    product_data = {
                        "id": pitch_data["product_id"],
                        "name": pitch_data["product_name"],
                        "features": "Features not available",
                        "fabric_details": "Fabric details not available",
                        "other_details": "Other details not available",
                        "price": "Price not available"
                    }
                    print(f"✅ Loaded limited product data from sales pitch: {product_data['name']}")
                    break
        except Exception as e:
            print(f"⚠️ Error loading from sales pitch data: {e}")
    
    # If still not found, create a minimal product data structure
    if product_data is None:
        print(f"⚠️ Creating minimal product data for ID {product_id}")
        product_data = {
            "id": product_id,
            "name": f"Product {product_id}",
            "features": "Features not available",
            "fabric_details": "Fabric details not available",
            "other_details": "An outdoor product from KETL Mtn. Apparel.",
            "price": "Price not available"
        }
    
    brand_voice = load_brand_voice()
    print(f"✅ Loaded brand voice guidelines")
    
    # Load original pitch if available
    original_pitch = None
    try:
        original_pitch = load_original_pitch(product_id)
        if original_pitch:
            print(f"✅ Loaded original sales pitch ({len(original_pitch)} chars)")
        else:
            print("ℹ️ No original sales pitch found for this product")
    except Exception as e:
        print(f"⚠️ Error loading original pitch: {e}")
    
    # Track iterations
    iterations: List[IterationData] = []
    previous_attempts: List[str] = []
    
    # Generate initial pitch
    current_pitch = await generate_sales_pitch(
        product_data, 
        brand_voice,
        original_pitch=original_pitch
    )
    iterations.append(IterationData(pitch=current_pitch))
    
    # Iterative refinement loop
    for i in range(max_iterations):
        print(f"\n📝 ITERATION {i+1}/{max_iterations}")
        
        # Evaluate current pitch
        evaluation = await evaluate_sales_pitch(current_pitch, product_data, brand_voice)
        iterations[-1].evaluation = evaluation
        
        # Check if evaluation passes
        if evaluation["status"] == "PASS":
            print(f"✅ Pitch meets all criteria after {i+1} iterations!")
            break
            
        # If not passing, collect feedback and try again
        previous_attempts.append(current_pitch)
        feedback = evaluation["feedback"]
        iterations[-1].feedback = feedback
        
        print(f"⚠️ Feedback: {feedback[:100]}...")
        
        # Generate improved pitch based on feedback
        current_pitch = await generate_sales_pitch(
            product_data, 
            brand_voice,
            previous_attempts,
            feedback,
            original_pitch
        )
        
        # Add new iteration to history
        iterations.append(IterationData(pitch=current_pitch))
    
    print("\n✨ Optimization workflow complete!")
    return current_pitch, iterations

async def main(product_id: int = 26):
    """
    Example usage of the evaluator-optimizer pattern.
    
    Args:
        product_id: ID of the product to optimize a sales pitch for (default: 26 - Vent Touch MTB Glove)
    """
    print(f"🎯 Optimizing sales pitch for product ID {product_id}")
    
    # Get product name if available
    product_name = f"Product {product_id}"
    try:
        data_dir = Path(__file__).parent.parent.parent / "common" / "ketlmtn_data"
        with open(data_dir / "ketlmtn_sales_pitch.json") as f:
            sales_pitches = json.load(f)
        
        for pitch_data in sales_pitches:
            if pitch_data.get("product_id") == product_id:
                product_name = pitch_data.get("product_name", f"Product {product_id}")
                break
        
        print(f"🏷️ Product: {product_name}")
    except Exception as e:
        print(f"⚠️ Error looking up product name: {e}")
    
    try:
        # Run the optimization workflow
        final_pitch, iterations = await optimize_sales_pitch(product_id, max_iterations=3)
        
        print("\n🏆 FINAL OPTIMIZED PITCH:")
        print(f"{final_pitch}")
        
        print(f"\n📊 Optimization took {len(iterations)} iterations")
        
        # Compare with original if available
        try:
            original_pitch = load_original_pitch(product_id)
            if original_pitch:
                print("\n📜 ORIGINAL PITCH FOR COMPARISON:")
                print(f"{original_pitch}")
                
                # Print word counts for comparison
                original_word_count = len(original_pitch.split())
                final_word_count = len(final_pitch.split())
                print(f"\n📏 Word count comparison:")
                print(f"  Original: {original_word_count} words")
                print(f"  Optimized: {final_word_count} words")
                print(f"  Difference: {final_word_count - original_word_count} words")
        except Exception as e:
            print(f"⚠️ Error loading original pitch for comparison: {e}")
    
    except Exception as e:
        print(f"❌ Error in optimization workflow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Parse command line arguments if provided
    import sys
    
    if len(sys.argv) > 1:
        try:
            product_id = int(sys.argv[1])
            asyncio.run(main(product_id))
        except ValueError:
            print(f"❌ Error: Product ID must be an integer. Got '{sys.argv[1]}'")
            print(f"Usage: python -m src.llm_composition_patterns.patterns.evaluator_optimizer.example [product_id]")
            sys.exit(1)
    else:
        # Use default product ID
        asyncio.run(main())
