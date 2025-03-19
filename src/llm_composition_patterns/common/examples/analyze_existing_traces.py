"""
Simple script to check available Phoenix projects and their spans.
"""
import os
from dotenv import load_dotenv
import phoenix as px
import pandas as pd  # type: ignore
from typing import Dict, Any

# Load environment variables
load_dotenv()

def print_span_attributes(span: pd.Series, indent: str = "") -> None:
    """Print all relevant attributes of a span."""
    print(f"\n{indent}Name: {span['name']}")
    
    # Calculate duration
    duration = pd.Timestamp(span['end_time']) - pd.Timestamp(span['start_time'])
    duration_s = duration.total_seconds()
    print(f"{indent}Duration: {duration_s:.2f}s")
    
    # Print input if it exists
    if 'attributes.input.value' in span:
        print(f"{indent}Input: {span['attributes.input.value']}")
    
    # Print output if it exists
    if 'attributes.output.value' in span:
        print(f"{indent}Output: {span['attributes.output.value']}")
    
    # For Completion spans, show LLM-specific info
    if span['name'] == 'Completions':
        print(f"{indent}Token Count: {span.get('attributes.llm.token_count', 'N/A')}")
        print(f"{indent}Provider: {span.get('attributes.llm.provider', 'N/A')}")
        if 'attributes.llm.messages' in span:
            print(f"{indent}Messages: {span['attributes.llm.messages']}")
    
    # Print all other attributes if they exist
    if 'attributes' in span and isinstance(span['attributes'], dict):
        attrs = span['attributes']
        print(f"{indent}Attributes:")
        for key, value in attrs.items():
            # Skip input/output if already printed
            if key not in ['input', 'output']:
                print(f"{indent}  {key}: {value}")
    
    # Print status if available
    if 'status_code' in span:
        print(f"{indent}Status: {span.get('status_code')} - {span.get('status_message', 'N/A')}")

def check_available_data() -> None:
    """Check what projects and data are available in Phoenix."""
    
    # Set up cloud connection
    api_key = os.environ.get("PHOENIX_API_KEY")
    if not api_key:
        raise ValueError("PHOENIX_API_KEY environment variable not set")
    
    os.environ["PHOENIX_CLIENT_HEADERS"] = f"api_key={api_key}"
    os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "https://app.phoenix.arize.com"
    
    client = px.Client(endpoint="https://app.phoenix.arize.com")
    
    # Get all spans for the project
    all_spans = client.get_spans_dataframe(project_name="llm-composition-routing")
    if all_spans is None or all_spans.empty:
        print("No spans found")
        return
    
    # Find root spans (routing_pattern)
    root_spans = all_spans[all_spans['name'] == 'routing_pattern']
    print(f"\nFound {len(root_spans)} routing patterns")
    
    for _, root_span in root_spans.iterrows():
        trace_id = root_span['context.trace_id']
        print(f"\n{'='*80}")
        print("LEVEL 1: Root Span (routing_pattern)")
        print("=" * 80)
        print_span_attributes(root_span)
        
        # Find step spans (children of root)
        steps = all_spans[
            (all_spans['context.trace_id'] == trace_id) & 
            (all_spans['parent_id'] == root_span['context.span_id']) &
            (all_spans['name'].str.startswith('step', na=False))
        ].sort_values('start_time')
        
        for _, step in steps.iterrows():
            print(f"\n{'-'*60}")
            print("LEVEL 2: Step")
            print("-" * 60)
            print_span_attributes(step, indent="  ")
            
            # Find completion spans (children of steps)
            completions = all_spans[
                (all_spans['context.trace_id'] == trace_id) &
                (all_spans['parent_id'] == step['context.span_id']) &
                (all_spans['name'] == 'Completions')
            ]
            
            for _, completion in completions.iterrows():
                print(f"\n{'.'*40}")
                print("LEVEL 3: Completion")
                print("." * 40)
                print_span_attributes(completion, indent="    ")
        
        print("\n")

if __name__ == "__main__":
    check_available_data() 