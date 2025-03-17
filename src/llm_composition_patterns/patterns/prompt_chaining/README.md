# Prompt Chaining Pattern

## Overview

The Prompt Chaining pattern creates a workflow where the output of one LLM call becomes the input for the next, forming a chain of prompts that work together to solve complex tasks. This pattern is useful when a task can be broken down into discrete steps that build upon each other.

## Implementation

This example demonstrates a 3-step prompt chain for a KETL Mtn. Apparel customer service chatbot:

1. **Query Relevance Filter**: Uses Llama Guard to determine if the query is relevant to KETL Mtn. products or outdoor activities.
2. **Product Information Lookup**: Searches a product database to find relevant information based on the customer's query.
3. **Brand Format Response**: Rewrites the product information in KETL Mtn.'s brand voice to create a concise, on-brand response.

## Key Components

- **`example.py`**: Main implementation of the prompt chaining pattern
- **`ketlmtn_products.json`**: Product database with details about KETL Mtn. products
- **`brand_voice.txt`**: Guidelines for KETL Mtn.'s brand voice and tone
- **`message_types.py`**: Common message type definitions for LLM interactions
- **`groq_helpers.py`/`fireworks_helpers.py`**: Helper functions for interacting with LLM providers

## Features

- **Modular Design**: Each step in the chain has a specific purpose and can be modified independently
- **Conversation History**: Maintains context across multiple interactions
- **Provider Flexibility**: Works with different LLM providers (Groq, Fireworks)
- **Concise Responses**: Optimized for chat-like interactions with brief, focused answers

## Usage

```python
# Initialize conversation
conversation_history = []

# Process a customer query
response, conversation_history = process_customer_query(
    "What mountain biking shorts do you recommend?", 
    conversation_history
)

# Process a follow-up question using the same conversation history
response, conversation_history = process_customer_query(
    "Do they come in black?", 
    conversation_history
)
```

## Benefits

- **Decomposition**: Breaks complex tasks into manageable steps
- **Specialization**: Each step can use a different model optimized for that task
- **Early Filtering**: Initial relevance filter screens out inappropriate or unrelated queries
- **Maintainability**: Each step can be updated independently

## Limitations

- **Latency**: Multiple API calls increase response time
- **Error Propagation**: Mistakes in early steps can affect later steps
- **Cost**: Multiple LLM calls increase usage costs

## Example Interactions

### Simple Query Example

```User: "I'm looking for lightweight hiking pants for summer."

Step 1: Filters query and confirms it's relevant to KETL Mtn. products
Step 2: Searches product database for lightweight hiking pants
Step 3: Brand formats response in KETL Mtn.'s voice and style

Response: "Hey there, trail seeker! Our Vent Lightweight Active Pants are perfect for summer hikes - super stretchy, breathable, and quick-drying. Available in Black, Grey, and Brown for $89.95. They've got zippered pockets and an anti-squish gusset design for ultimate comfort on the trail!"
```