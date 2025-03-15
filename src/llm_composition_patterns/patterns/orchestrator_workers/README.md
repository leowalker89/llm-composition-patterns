# Orchestrator-Workers Pattern

## Overview

The Orchestrator-Workers pattern breaks down complex tasks into specialized subtasks that are handled by dedicated worker LLMs, with results synthesized into a cohesive output. This pattern is useful when a task requires multiple types of expertise or analysis that can be delegated to specialized components. By dynamically decomposing tasks and assigning them to appropriate workers, the system can provide more comprehensive and accurate responses.

## Implementation

This example demonstrates an orchestrator-workers pattern for a KETL Mtn. Apparel product recommendation system:

1. **Task Orchestration**: Uses an LLM to analyze customer queries and break them down into specialized subtasks
2. **Specialized Workers**: Routes subtasks to dedicated worker LLMs:
   - Customer profile analysis worker (extracts customer needs and preferences)
   - Product matching worker (finds products that match the customer profile)
3. **Result Synthesis**: Combines worker outputs into a cohesive, personalized recommendation in KETL Mtn.'s brand voice

## Key Components

- **`example.py`**: Main implementation of the orchestrator-workers pattern
- **`ketlmtn_products.json`**: Product database with details about KETL Mtn. products
- **`brand_voice.txt`**: Guidelines for KETL Mtn.'s brand voice and tone
- **`groq_helpers.py`**: Helper functions for interacting with LLM providers
- **`message_types.py`**: Common message type definitions for LLM interactions

## Features

- **Dynamic Task Decomposition**: Analyzes queries to determine necessary subtasks
- **Specialized Processing**: Uses dedicated workers for different aspects of the recommendation process
- **Structured Data Flow**: Maintains clear data structures between components
- **Robust Error Handling**: Includes fallbacks for JSON parsing errors and LLM failures
- **Consistent Brand Voice**: All final recommendations maintain KETL Mtn.'s brand identity

## Usage

```python
# Initialize the recommendation workflow
query = "I need lightweight hiking gear for a summer trek in Colorado."
recommendation = await recommendation_workflow(query)
print(recommendation)
```

## Benefits

- **Expertise Specialization**: Each worker can focus on a specific aspect of the task
- **Adaptability**: Dynamically determines required subtasks based on the query
- **Maintainability**: Workers can be updated independently
- **Comprehensive Analysis**: Combines multiple perspectives for better recommendations
- **Scalability**: Easy to add new worker types for additional capabilities

## Limitations

- **Coordination Complexity**: Requires careful orchestration of multiple components
- **Potential Latency**: Multiple LLM calls increase overall response time
- **Error Propagation**: Errors in early stages can affect downstream workers
- **Integration Challenges**: Ensuring consistent data formats between components

## Example Interactions

### Product Recommendation Example
