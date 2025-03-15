"""
Arize Phoenix setup for tracing LLM interactions.

This module provides functions to set up OpenTelemetry tracing with Arize Phoenix
for monitoring and debugging LLM applications.
"""

import os
from typing import Optional
from opentelemetry import trace as trace_api
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter #type: ignore
from openinference.semconv.resource import ResourceAttributes
from openinference.instrumentation.groq import GroqInstrumentor

def setup_tracing(
    project_name: str,
    api_key: Optional[str] = None,
    endpoint: str = "https://app.phoenix.arize.com/v1/traces",
    enable_local: bool = False
) -> trace_sdk.TracerProvider:
    """
    Set up OpenTelemetry tracing with Arize Phoenix for Groq LLM calls.
    
    Args:
        project_name: Name of the project for grouping traces
        api_key: Arize Phoenix API key (defaults to PHOENIX_API_KEY env var)
        endpoint: Trace collection endpoint
        enable_local: If True, also send traces to a local Phoenix instance
        
    Returns:
        Configured tracer provider
    """
    # Get API key from environment if not provided
    if api_key is None:
        api_key = os.environ.get("PHOENIX_API_KEY")
        if not api_key and not enable_local:
            raise ValueError(
                "API key must be provided either as an argument or via PHOENIX_API_KEY environment variable"
            )
    
    # Create resource with project name
    resource = Resource.create({
        ResourceAttributes.PROJECT_NAME: project_name
    })
    
    # Create tracer provider with resource
    tracer_provider = trace_sdk.TracerProvider(resource=resource)
    
    # Set up Arize Phoenix cloud exporter if API key is available
    if api_key:
        headers = {"api_key": api_key}
        cloud_exporter = OTLPSpanExporter(
            endpoint=endpoint,
            headers=headers
        )
        tracer_provider.add_span_processor(SimpleSpanProcessor(cloud_exporter))
        print(f"✅ Configured Arize Phoenix cloud tracing for project: {project_name}")
    
    # Set up local Phoenix exporter if enabled
    if enable_local:
        local_endpoint = "http://localhost:6006/v1/traces"
        local_exporter = OTLPSpanExporter(endpoint=local_endpoint)
        tracer_provider.add_span_processor(SimpleSpanProcessor(local_exporter))
        print(f"✅ Configured local Phoenix tracing at {local_endpoint}")
    
    # Set global tracer provider
    trace_api.set_tracer_provider(tracer_provider)
    
    # Instrument Groq client
    GroqInstrumentor().instrument(tracer_provider=tracer_provider)
    print("✅ Instrumented Groq client for tracing")
    
    return tracer_provider

def enable_tracing_for_pattern(pattern_name: str) -> trace_sdk.TracerProvider:
    """
    Convenience function to enable tracing for a specific pattern example.
    
    Args:
        pattern_name: Name of the pattern (e.g., "prompt_chaining", "routing")
        
    Returns:
        Configured tracer provider
    """
    project_name = f"llm-composition-{pattern_name}"
    
    # Check if we're in a local development environment
    enable_local = os.environ.get("PHOENIX_LOCAL", "false").lower() == "true"
    
    return setup_tracing(
        project_name=project_name,
        enable_local=enable_local
    ) 