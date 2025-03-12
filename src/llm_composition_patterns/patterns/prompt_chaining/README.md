# Prompt Chaining Pattern

## Overview

The Prompt Chaining pattern creates a workflow where the output of one LLM call becomes the input for the next, forming a chain of prompts that work together to solve complex tasks. This pattern is useful when a task can be broken down into discrete steps that build upon each other.

## Implementation

This example demonstrates a 3-step prompt chain for a KETL Mtn. Apparel customer service chatbot:

1. **Query Validation**: Uses Llama Guard to determine if the query is appropriate and related to KETL Mtn. products or outdoor activities.
2. **Product Information Lookup**: Searches a product database to find relevant information based on the customer's query.
3. **Response Formatting**: Rewrites the product information in KETL Mtn.'s brand voice to create a concise, on-brand response.

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
- **Error Handling**: Early steps can filter out inappropriate queries
- **Maintainability**: Each step can be updated independently

## Limitations

- **Latency**: Multiple API calls increase response time
- **Error Propagation**: Mistakes in early steps can affect later steps
- **Cost**: Multiple LLM calls increase usage costs

## Example Interactions

### Simple Query Example

```
User: "I'm looking for lightweight hiking pants for summer."

Step 1: Validates query is appropriate and related to KETL Mtn. products
Step 2: Searches product database for lightweight hiking pants
Step 3: Formats response in KETL Mtn.'s brand voice

Response: "Hey there, trail seeker! Our Vent Lightweight Active Pants are perfect for summer hikes - super stretchy, breathable, and quick-drying. Available in Black, Grey, and Brown for $89.95. They've got zippered pockets and an anti-squish gusset design for ultimate comfort on the trail!"
```

### Conversation Flow Example

```
User: "I need a new set of gloves for riding in Colorado this summer."

Response: "Hey adventurer! Our Vent Touch MTB Glove is perfect for Colorado trails. Lightweight mesh back, silicone grip, and touchscreen compatible. Available in Black or Teal, sizes S-XXL for $34.95. Ready to ride?"

User: "Do you have any other gloves?"

Response: "Sorry, the Vent Touch MTB Glove is our only option right now. It's got a breathable mesh back, grippy silicone fingers, and touchscreen compatibility. Available in Black or Teal for $34.95."

User: "What about socks?"

Response: "Our Merino Wool socks are perfect for trail riding! We have Warmweather Quick-Dry, Coolweather Cushioned, and Fairweather All-Season options - all $24.95. They're moisture-wicking, breathable, and super comfy with seamless toe caps."
```

## Running the Example

To run the example:

1. Ensure you have the required dependencies:
   ```bash
   uv add groq python-dotenv
   ```

2. Set up your environment variables:
   ```bash
   # Create a .env file with your API key
   echo "GROQ_API_KEY=your_api_key_here" > .env
   ```

3. Run the example:
   ```bash
   python -m src.llm_composition_patterns.patterns.prompt_chaining.example
   ```
