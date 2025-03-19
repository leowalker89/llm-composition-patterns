"""
Evaluator-Optimizer pattern for iteratively improving sales pitches.

This pattern demonstrates how to generate and iteratively refine content
through alternating generation and evaluation steps.
"""

import json
import asyncio
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add tracing setup BEFORE importing any modules that use Groq
from llm_composition_patterns.common.arize_phoenix_setup import enable_tracing_for_pattern
from opentelemetry import trace  # type: ignore

# Enable tracing for this pattern
tracer_provider = enable_tracing_for_pattern("evaluator_optimizer")  # type: ignore
tracer = trace.get_tracer("evaluator_optimizer")  # type: ignore

# Now import the rest of the modules
from llm_composition_patterns.common.groq_helpers import run_llm_async
from llm_composition_patterns.common.ketlmtn_helpers import (
    load_products, 
    get_product_by_id,
    load_brand_voice_text,
    get_sales_pitch_by_id
)
from llm_composition_patterns.common.models import ProductData, EvaluationResult

@dataclass
class IterationData:
    """Data for tracking an iteration of the optimization process."""
    pitch: str
    evaluation: Optional[EvaluationResult] = None

async def generate_pitch(
    product: ProductData, 
    brand_voice: str,
    feedback: Optional[str] = None
) -> str:
    """
    Generate or improve a sales pitch.
    
    Args:
        product: Product details
        brand_voice: KETL brand voice guidelines
        feedback: Optional feedback from previous evaluation
        
    Returns:
        Generated sales pitch text
    """
    with tracer.start_as_current_span("generate_pitch"):
        print(f"\nGenerating pitch for {product.name}" + 
              (f" with feedback" if feedback else ""))
        
        # Create prompt
        system_prompt = f"""
        You are an expert copywriter for KETL Mtn. Apparel, creating compelling sales pitches.
        
        PRODUCT INFORMATION:
        {json.dumps(product.model_dump(), indent=2)}
        
        BRAND VOICE GUIDELINES:
        {brand_voice}
        
        {f"FEEDBACK FROM PREVIOUS EVALUATION:\n{feedback}" if feedback else ""}
        
        Create a concise, compelling sales pitch (around 75-100 words) that:
        - Uses authentic, conversational language aligned with KETL's brand voice
        - Highlights key product features and benefits
        - Mentions our lifetime repair guarantee and free shipping/returns
        - Is technically accurate based on the product data
        - Is persuasive and drives action
        """
        
        response = await run_llm_async(
            user_prompt="Generate a compelling sales pitch for this product.",
            system_prompt=system_prompt,
            model="llama-3.3-70b-versatile"
        )
        
        return response.strip() if response else f"[Placeholder pitch for {product.name}]"

async def evaluate_pitch(pitch: str, product: ProductData, brand_voice: str) -> EvaluationResult:
    """
    Evaluate a sales pitch against KETL brand guidelines and effectiveness criteria.
    
    Args:
        pitch: The sales pitch to evaluate
        product: Product data
        brand_voice: KETL brand voice guidelines
        
    Returns:
        Evaluation results with pass/fail status and feedback
    """
    with tracer.start_as_current_span("evaluate_pitch"):
        print(f"\nEvaluating pitch for {product.name}")
        
        # Move instructions and context to system prompt
        system_prompt = f"""
        You are a quality assurance specialist for KETL Mtn. Apparel, evaluating sales pitches.
        
        PRODUCT INFORMATION:
        {json.dumps(product.model_dump(), indent=2)}
        
        BRAND VOICE GUIDELINES:
        {brand_voice}
        
        Evaluate if the pitch meets our requirements for:
        1. Brand Voice: Authentic, conversational, aligned with KETL's voice
        2. Feature Completeness: Covers key product features and benefits
        3. Technical Accuracy: All claims are factually correct
        4. Persuasiveness: Compelling and likely to drive action
        5. Policy Mention: Includes lifetime repair guarantee and shipping/returns
        6. Conciseness: Around 75-100 words (speakable in ~30 seconds)
        
        Return a JSON object with this structure:
        {{
          "status": "PASS" or "NEEDS_IMPROVEMENT",
          "feedback": "Detailed feedback explaining issues and suggesting improvements"
        }}
        
        Only return "PASS" if the pitch meets ALL the criteria.
        """
        
        # Move the sales pitch to evaluate into the user message
        user_prompt = f"""
        Please evaluate this sales pitch:

        {pitch}
        """
        
        response = await run_llm_async(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            model="llama-3.3-70b-versatile"
        )
        
        # Handle parsing with simpler error handling
        try:
            # Handle None response
            if not response:
                return EvaluationResult(
                    status="NEEDS_IMPROVEMENT",
                    feedback="Unable to evaluate pitch. Please improve clarity and completeness."
                )
                
            # Extract JSON if wrapped in markdown or extra text
            import re
            json_match = re.search(r'({.*})', response.replace('\n', ' '))
            json_str = json_match.group(1) if json_match else response
            
            # Parse with Pydantic
            result = EvaluationResult.model_validate_json(json_str)
            
            # Print key info
            print(f"Evaluation status: {result.status}")
            
            return result
            
        except Exception as e:
            # Simple fallback for parsing errors
            return EvaluationResult(
                status="NEEDS_IMPROVEMENT",
                feedback=f"Error parsing evaluation: {str(e)}. Please improve the pitch."
            )

async def main(product_id: Optional[int] = 5, max_iterations: int = 3):
    """
    Run the evaluator-optimizer pattern to generate an optimized sales pitch.
    
    Args:
        product_id: ID of the product to create a pitch for (defaults to 5)
        max_iterations: Maximum number of refinement iterations
        
    Returns:
        Tuple of (final_pitch, iteration_history)
    """
    # Create a single parent span for the entire process
    with tracer.start_as_current_span("evaluator_optimizer") as span:
        product_id_value = product_id if product_id is not None else 5
        span.set_attribute("product_id", product_id_value)
        span.set_attribute("pattern", "evaluator_optimizer")
        
        print(f"\n=== Starting Evaluator-Optimizer Pattern for Product {product_id_value} ===")
        
        # Load product data - simplified approach
        # Try main product database first
        product = get_product_by_id(product_id_value, load_products())
        
        if product:
            product_data = ProductData(
                id=product["product_id"],
                name=product["extracted_data"]["product_name"],
                features=product["extracted_data"].get("product_features", ""),
                details=product["extracted_data"].get("other_details", ""),
                fabric_details=product["extracted_data"].get("fabric_details", ""),
                price=str(product["extracted_data"].get("price", "")),
                colors=product["extracted_data"].get("available_colors", []),
                sizes=product["extracted_data"].get("available_sizes", [])
            )
        else:
            # Try sales pitch database
            pitch = get_sales_pitch_by_id(product_id_value)
            
            if pitch:
                product_data = ProductData(
                    id=pitch["product_id"],
                    name=pitch["product_name"]
                )
            else:
                # Fallback
                product_data = ProductData(
                    id=product_id_value,
                    name=f"Product {product_id_value}"
                )
        
        brand_voice = load_brand_voice_text()
        print(f"Loaded data for product: {product_data.name}")
        
        # Initialize tracking
        iterations = []
        
        # Generate initial pitch
        current_pitch = await generate_pitch(product_data, brand_voice)
        iterations.append(IterationData(pitch=current_pitch))
        
        # Refinement loop - THE CORE OF THE PATTERN
        for i in range(max_iterations):
            print(f"\n--- Iteration {i+1}/{max_iterations} ---")
            
            # Evaluate current pitch
            evaluation = await evaluate_pitch(current_pitch, product_data, brand_voice)
            iterations[-1].evaluation = evaluation
            
            # Check if successful
            if evaluation.is_successful():
                print(f"Success! Pitch meets all criteria after {i+1} iterations.")
                span.set_attribute("iterations_needed", i+1)
                break
            
            # Exit if we've reached max iterations
            if i >= max_iterations - 1:
                print("Reached maximum iterations.")
                break
                
            # Generate improved pitch with feedback
            print(f"Feedback: {evaluation.feedback[:100]}..." if len(evaluation.feedback) > 100 
                  else f"Feedback: {evaluation.feedback}")
            
            current_pitch = await generate_pitch(
                product_data, 
                brand_voice,
                feedback=evaluation.feedback
            )
            iterations.append(IterationData(pitch=current_pitch))
        
        # Record final outcome
        span.set_attribute("total_iterations", len(iterations))
        
        # Print results
        print(f"\n=== Final Pitch ===\n")
        print(current_pitch)
        print("\n=== End of Process ===")
        
        return current_pitch, iterations

if __name__ == "__main__":
    # Simple command line handling
    product_id = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    asyncio.run(main(product_id=product_id))
