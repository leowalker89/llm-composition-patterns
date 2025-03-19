"""
Utilities for querying and analyzing Arize Phoenix traces.

Provides essential functions to retrieve and analyze trace data from 
Phoenix for LLM composition patterns.
"""
from typing import Dict, List, Optional, Any, Union, cast
import pandas as pd  # type: ignore
import phoenix as px


def get_traces_df(
    filter_query: Optional[str] = None,
    limit: int = 1000
) -> pd.DataFrame:
    """
    Retrieve spans from Arize Phoenix as a pandas DataFrame.
    
    Args:
        filter_query: Optional filter query string (e.g., 'span_kind == "LLM"')
        limit: Maximum number of spans to retrieve
        
    Returns:
        DataFrame containing the requested spans
    
    Example:
        >>> df = get_traces_df('root_span.name == "prompt_chaining"')
    """
    client = px.Client()
    
    # Get the spans dataframe with the filter if provided
    if filter_query:
        return client.get_spans_dataframe(filter_query)
    return client.get_spans_dataframe()


def get_pattern_traces(
    pattern_name: str,
    limit: int = 100
) -> pd.DataFrame:
    """
    Get traces specific to a pattern type.
    
    Args:
        pattern_name: Name of the pattern to filter traces for
        limit: Maximum number of spans to retrieve
        
    Returns:
        DataFrame containing traces for the specified pattern
    """
    filter_query = f'root_span.name == "{pattern_name}"'
    return get_traces_df(filter_query)


def extract_span_attributes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract span attributes into separate columns for easier analysis.
    
    Args:
        df: DataFrame containing spans from Arize Phoenix
        
    Returns:
        DataFrame with span attributes expanded into columns
    """
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # Check if we have an attributes column
    if 'attributes' not in result_df.columns:
        return result_df
    
    # Extract common attributes into their own columns
    common_attrs = [
        'model', 'prompt', 'completion', 'temperature', 
        'duration_ms', 'query', 'response', 'error'
    ]
    
    for attr in common_attrs:
        result_df[attr] = result_df['attributes'].apply(
            lambda attrs: attrs.get(attr, None) if isinstance(attrs, dict) else None
        )
    
    return result_df


def compare_patterns(
    patterns: List[str],
    metric: str = "duration_ms",
    limit_per_pattern: int = 50
) -> pd.DataFrame:
    """
    Compare metrics across different patterns.
    
    Args:
        patterns: List of pattern names to compare
        metric: Metric to compare (default: duration_ms)
        limit_per_pattern: Maximum traces to retrieve per pattern
        
    Returns:
        DataFrame with comparative metrics
    """
    results = []
    
    for pattern in patterns:
        # Get traces for this pattern
        pattern_df = get_pattern_traces(pattern)
        
        if not pattern_df.empty:
            # Extract the metric from attributes if needed
            pattern_df = extract_span_attributes(pattern_df)
            
            # Add pattern name for grouping
            pattern_df['pattern'] = pattern
            results.append(pattern_df)
    
    if results:
        return pd.concat(results)
    return pd.DataFrame() 