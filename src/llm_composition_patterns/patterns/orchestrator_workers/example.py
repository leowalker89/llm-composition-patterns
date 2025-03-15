"""
Orchestrator-Workers pattern implementation for KETL Mtn. product recommendations.

This module demonstrates an advanced LLM composition pattern where an orchestrator
breaks down complex product recommendation tasks into subtasks handled by specialized
workers, with results synthesized into a final recommendation.
"""

import json
import asyncio
import os
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import sys

# Add this at the top of your file to debug
print(f"Current directory: {os.getcwd()}")
print(f"File location: {os.path.dirname(os.path.abspath(__file__))}")

# List directories to find the correct path
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
print(f"Src directory: {src_dir}")
print(f"Contents of src: {os.listdir(src_dir)}")

# Fix the import path by adding the src directory to sys.path
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Now use imports relative to src
from llm_composition_patterns.common.groq_helpers import run_llm_async
from llm_composition_patterns.common.message_types import ChatMessage  # type: ignore

# Load environment variables
load_dotenv()

@dataclass
class TaskDefinition:
    """Structured definition of a worker task."""
    task_type: str
    description: str
    required_inputs: List[str]
    expected_output: str

@dataclass
class WorkerResult:
    """Results from a worker's task execution."""
    task_type: str
    result: Dict
    confidence: float

def load_data() -> Tuple[List[Dict], str]:
    """Load product catalog and brand voice guidelines."""
    data_dir = Path(__file__).parent.parent.parent / "common" / "ketlmtn_data"
    
    with open(data_dir / "ketlmtn_products.json") as f:
        products = json.load(f)
    
    with open(data_dir / "brand_voice.txt") as f:
        brand_voice = f.read()
    
    print(f"✅ Loaded {len(products)} products and brand voice guidelines")
    return products, brand_voice

# Add this helper function to extract JSON from markdown responses
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

async def orchestrate_recommendation(query: str) -> List[TaskDefinition]:
    """Analyze customer query and break it down into specialized tasks."""
    print("\n🔍 ORCHESTRATOR: Breaking down query into specialized tasks...")
    
    system_prompt = """
    You are a task planning expert. Analyze the customer query and break it down into
    specialized tasks for product recommendations. Focus on understanding customer needs,
    matching products, and suggesting alternatives.
    
    Return a JSON array of tasks, each with:
    - task_type: The type of analysis needed (use "profile_analysis" for customer profile and "product_matching" for product matching)
    - description: Detailed description of the task
    - required_inputs: List of required input data
    - expected_output: Description of expected output format
    
    Example response format:
    [
      {
        "task_type": "profile_analysis",
        "description": "Analyze customer needs and preferences",
        "required_inputs": ["query"],
        "expected_output": "Customer profile JSON"
      },
      {
        "task_type": "product_matching",
        "description": "Find products matching customer profile",
        "required_inputs": ["profile", "products"],
        "expected_output": "Matched products JSON"
      }
    ]
    """
    
    response = await run_llm_async(
        user_prompt=query,
        system_prompt=system_prompt,
        model="llama-3.1-8b-instant"
    )
    
    if not response:
        raise Exception("Failed to get response from LLM")
    
    print(f"📄 Raw orchestrator response:\n{response[:200]}...\n")
    
    try:
        json_str = extract_json_from_response(response)
        tasks = json.loads(json_str)
        task_definitions = [TaskDefinition(**task) for task in tasks]
        
        print(f"✅ Created {len(task_definitions)} tasks:")
        for i, task in enumerate(task_definitions):
            print(f"  {i+1}. {task.task_type}: {task.description}")
        
        return task_definitions
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON decode error: {e}")
        print(f"⚠️ Using default tasks instead")
        
        # Return default tasks if JSON parsing fails
        default_tasks = [
            TaskDefinition(
                task_type="profile_analysis",
                description="Analyze customer profile and needs",
                required_inputs=["query"],
                expected_output="Customer profile JSON"
            ),
            TaskDefinition(
                task_type="product_matching",
                description="Match products to customer profile",
                required_inputs=["profile", "products"],
                expected_output="Matched products JSON"
            )
        ]
        
        print(f"✅ Created {len(default_tasks)} default tasks:")
        for i, task in enumerate(default_tasks):
            print(f"  {i+1}. {task.task_type}: {task.description}")
            
        return default_tasks

async def analyze_customer_profile(query: str, task: TaskDefinition) -> WorkerResult:
    """Extract customer preferences, activities, and environmental needs."""
    print(f"\n👤 WORKER: Analyzing customer profile...")
    
    system_prompt = """
    You are a customer needs analyst. Extract key information about the customer's:
    - Activities and use cases
    - Environmental conditions
    - Performance requirements
    - Style preferences
    
    Return a JSON object with structured profile information.
    
    Example response format:
    {
      "activities": ["hiking", "trekking"],
      "environment": {"location": "Colorado", "season": "summer", "conditions": "hot, dry"},
      "requirements": ["lightweight", "breathable", "durable"],
      "style_preferences": ["functional", "minimalist"]
    }
    """
    
    response = await run_llm_async(
        user_prompt=query,
        system_prompt=system_prompt,
        model="llama-3.1-8b-instant"
    )
    
    if not response:
        raise Exception("Failed to get response from LLM")
    
    print(f"📄 Raw profile analysis response:\n{response[:200]}...\n")
    
    try:
        json_str = extract_json_from_response(response)
        result = json.loads(json_str)
        
        print("✅ Profile analysis complete. Key insights:")
        for key, value in result.items():
            if isinstance(value, list):
                print(f"  {key}: {', '.join(value[:3])}" + ("..." if len(value) > 3 else ""))
            elif isinstance(value, dict):
                print(f"  {key}: {list(value.keys())}")
            else:
                print(f"  {key}: {value}")
    except json.JSONDecodeError:
        print("⚠️ JSON parsing failed, using fallback profile")
        # Fallback if JSON parsing fails
        result = {
            "activities": ["hiking", "trekking"],
            "environment": {"location": "Colorado", "season": "summer"},
            "requirements": ["lightweight"]
        }
    
    return WorkerResult(
        task_type="profile_analysis",
        result=result,
        confidence=0.9
    )

async def match_products(profile: Dict, products: List[Dict], task: TaskDefinition) -> WorkerResult:
    """Identify products matching customer requirements."""
    print(f"\n🔍 WORKER: Matching products to customer profile...")
    
    system_prompt = """
    You are a product matching specialist. Find KETL Mtn. products that best match
    the customer profile. Consider:
    - Activity compatibility
    - Environmental suitability
    - Performance requirements
    - Style preferences
    
    Return a JSON object with ranked product matches and reasoning.
    
    Example response format:
    {
      "matches": [
        {
          "product_id": 12,
          "product_name": "Lightweight Hiking Pants",
          "match_score": 0.95,
          "reasoning": "Perfect for summer hiking in Colorado due to lightweight, breathable fabric"
        }
      ],
      "alternatives": [
        {
          "product_id": 8,
          "product_name": "All-Weather Hiking Jacket",
          "match_score": 0.75,
          "reasoning": "Good for unexpected weather changes in mountain environments"
        }
      ]
    }
    """
    
    # Limit products to avoid token limits
    sample_products = products[:20]
    
    user_prompt = json.dumps({
        "profile": profile, 
        "products": sample_products
    })
    
    response = await run_llm_async(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model="llama-3.1-8b-instant"
    )
    
    if not response:
        raise Exception("Failed to get response from LLM")
    
    print(f"📄 Raw product matching response:\n{response[:200]}...\n")
    
    try:
        json_str = extract_json_from_response(response)
        result = json.loads(json_str)
        
        print("✅ Product matching complete. Top matches:")
        if "matches" in result and result["matches"]:
            for i, match in enumerate(result["matches"][:3]):
                print(f"  {i+1}. {match.get('product_name', 'Unknown')} (Score: {match.get('match_score', 'N/A')})")
                if "reasoning" in match:
                    print(f"     Reason: {match['reasoning'][:100]}...")
        else:
            print("  No specific matches found")
    except json.JSONDecodeError:
        print("⚠️ JSON parsing failed, using fallback matches")
        # Fallback if JSON parsing fails
        result = {
            "matches": [{"product_id": 1, "product_name": "Example Product", "match_score": 0.8}],
            "alternatives": []
        }
    
    return WorkerResult(
        task_type="product_matching",
        result=result,
        confidence=0.85
    )

async def synthesize_recommendation(query: str, worker_results: List[WorkerResult], brand_voice: str) -> str:
    """Combine worker outputs into a cohesive recommendation."""
    print(f"\n🔄 SYNTHESIZER: Creating final recommendation...")
    
    system_prompt = f"""
    You are KETL Mtn.'s product recommendation specialist. Create a personalized
    recommendation using the analysis results. Follow our brand voice guidelines:
    
    {brand_voice}
    """
    
    user_prompt = json.dumps({
        "query": query,
        "results": [r.result for r in worker_results]
    })
    
    response = await run_llm_async(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model="llama-3.1-8b-instant"
    )
    
    if not response:
        return "Sorry, I couldn't generate a recommendation at this time."
    
    print(f"📄 Raw synthesis response:\n{response[:200]}...\n")
    print("✅ Final recommendation generated")
    
    return response

async def recommendation_workflow(query: str) -> str:
    """Execute the full orchestrator-workers pattern workflow."""
    print("\n🚀 Starting orchestrator-workers workflow...")
    
    # Load necessary data
    products, brand_voice = load_data()
    
    # Use orchestrator to analyze query and create tasks
    try:
        tasks = await orchestrate_recommendation(query)
    except Exception as e:
        print(f"❌ Error in orchestration: {e}")
        # Fallback to default tasks
        tasks = [
            TaskDefinition(
                task_type="profile_analysis",
                description="Analyze customer profile and needs",
                required_inputs=["query"],
                expected_output="Customer profile JSON"
            ),
            TaskDefinition(
                task_type="product_matching",
                description="Match products to customer profile",
                required_inputs=["profile", "products"],
                expected_output="Matched products JSON"
            )
        ]
    
    # Execute worker tasks
    try:
        profile_task = next((t for t in tasks if t.task_type == "profile_analysis"), tasks[0])
        profile_result = await analyze_customer_profile(query, profile_task)
        
        matching_task = next((t for t in tasks if t.task_type == "product_matching"), tasks[1])
        matching_result = await match_products(
            profile_result.result,
            products,
            matching_task
        )
        
        # Synthesize final recommendation
        final_recommendation = await synthesize_recommendation(
            query,
            [profile_result, matching_result],
            brand_voice
        )
        
        print("\n✨ Workflow complete!")
        return final_recommendation
    except Exception as e:
        print(f"❌ Error in workflow: {e}")
        return f"Sorry, I encountered an error while processing your request: {str(e)}"

async def main():
    """Example usage of the orchestrator-workers pattern."""
    query = "I need lightweight hiking gear for a summer trek in Colorado."
    print(f"\n📝 Customer Query: {query}\n")
    
    try:
        recommendation = await recommendation_workflow(query)
        print(f"\n📣 Final Recommendation:\n{recommendation}")
    except Exception as e:
        print(f"❌ Error generating recommendation: {e}")

if __name__ == "__main__":
    asyncio.run(main())
