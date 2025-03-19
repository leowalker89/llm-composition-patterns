# Common Utilities

This directory contains shared utilities and models used across different LLM composition patterns.

## Overview

The `common` directory provides reusable components that maintain consistency and reduce duplication across pattern implementations. These components handle common tasks like:

- LLM provider interactions (Groq, Fireworks)
- Data loading and processing for KETL Mtn. examples
- Structured data models with validation
- Tracing and observability setup

## Key Components

### LLM Provider Utilities

- **`groq_helpers.py`**: Functions for interacting with Groq LLM API
  - `run_llm()`: Synchronous API call function
  - `run_llm_async()`: Asynchronous API call function

- **`fireworks_helpers.py`**: Functions for interacting with Fireworks LLM API
  - Similar interface to Groq helpers for provider flexibility

### Data Models

- **`models.py`**: Pydantic models for structured data
  - `ProductData`: Product information with validation
  - `EvaluationCriteria`: Evaluation criterion with score and feedback
  - `EvaluationResult`: Evaluation outcome with criteria and pass/fail status

- **`message_types.py`**: Type definitions for message formats
  - `ChatMessage`: Compatible with various LLM providers

### KETL Mountain Data Utilities

- **`ketlmtn_helpers.py`**: Functions for loading and processing KETL Mtn. data
  - Product loading from JSON files
  - Company and warranty information loading
  - Brand voice guidelines access
  - Sales pitch retrieval and formatting

### Observability

- **`arize_phoenix_setup.py`**: OpenTelemetry setup for tracing
  - `setup_tracing()`: Configures tracing with Arize Phoenix
  - `enable_tracing_for_pattern()`: Convenience function for pattern-specific tracing

## Data Files

The `ketlmtn_data/` directory contains sample data files:
- Product information
- Brand voice guidelines
- Company information
- Warranty details
- Example sales pitches

## Usage

These utilities are imported and used by each pattern implementation. For example:

```python
# Import LLM provider helper
from llm_composition_patterns.common.groq_helpers import run_llm_async

# Import data utilities
from llm_composition_patterns.common.ketlmtn_helpers import (
    load_products,
    get_product_by_id
)

# Import models for structured data
from llm_composition_patterns.common.models import ProductData, EvaluationResult

# Set up tracing
from llm_composition_patterns.common.arize_phoenix_setup import enable_tracing_for_pattern
tracer_provider = enable_tracing_for_pattern("pattern_name")
```

## Best Practices

When extending this repository:

1. Add new shared functionality to the appropriate existing file or create a new one if needed
2. Maintain consistent interfaces for similar functions
3. Use Pydantic models for data validation and structure
4. Document the purpose and usage of each component 