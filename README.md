# LLM Composition Patterns

A practical demonstration of LLM workflow patterns and agent architectures inspired by Anthropic's "Building Effective Agents" article.

## Overview

This project offers interactive examples and implementations of LLM workflow patterns and agent architectures, drawing inspiration from Anthropic's blog post ["Building Effective Agents"](https://www.anthropic.com/engineering-at-anthropic/building-effective-agents) (December 2024) and resources like [Agent Recipes](https://www.agentrecipes.com/). It aims to help developers understand and implement these patterns in their applications.

The example implementations use Python 3.12+, Groq's LLM API, and Arize Phoenix for tracing and observability. All examples are built around a fictional outdoor apparel company called "KETL Mtn. Apparel" to provide consistent, realistic scenarios.

## Patterns

The repository includes the following patterns:

### [Parallelization](src/llm_composition_patterns/patterns/parallelization/)
Executing multiple LLM tasks concurrently to reduce total processing time. Demonstrated through product description translation into multiple languages simultaneously.

### [Prompt Chaining](src/llm_composition_patterns/patterns/prompt_chaining/)
Creating a workflow where the output of one LLM call becomes the input for the next, forming a sequential chain. Demonstrated through a customer service chatbot that filters, processes, and formats responses.

### [Routing](src/llm_composition_patterns/patterns/routing/)
Directing user queries to specialized handlers based on the type of information requested. Demonstrated through a customer service chatbot that routes questions to product, company, or warranty specialists.

### [Evaluator-Optimizer](src/llm_composition_patterns/patterns/evaluator_optimizer/)
Implementing an iterative improvement cycle where content is repeatedly generated, evaluated, and refined. Demonstrated through generating and refining sales pitches based on quality criteria.

### [Orchestrator-Workers](src/llm_composition_patterns/patterns/orchestrator_workers/) (Coming Soon)
Using a coordinator LLM to manage a team of specialized worker LLMs. Implementation coming soon.

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) for package management
- Groq API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/llm-composition-patterns.git
   cd llm-composition-patterns
   ```

2. Create and activate a virtual environment:
   ```bash
   uv venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   uv add -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env to add your API keys
   ```

### Running an Example

Choose a pattern and run its example:

```bash
# Example for the Parallelization pattern
python -m src.llm_composition_patterns.patterns.parallelization.example
```

## Project Structure

- `src/llm_composition_patterns/`
  - `patterns/`: Implementation of different patterns
    - `parallelization/`: Parallelization pattern
    - `prompt_chaining/`: Prompt chaining pattern
    - `routing/`: Routing pattern
    - `evaluator_optimizer/`: Evaluator-optimizer pattern
    - `orchestrator_workers/`: Orchestrator-workers pattern (coming soon)
  - `common/`: Shared utilities and models
    - `groq_helpers.py`: Helper functions for Groq API
    - `models.py`: Shared Pydantic models
    - `ketlmtn_helpers.py`: Utilities for KETL Mtn. examples
    - `arize_phoenix_setup.py`: Tracing setup
    - `ketlmtn_data/`: Sample data files

## Tracing and Observability

All examples use OpenTelemetry with Arize Phoenix for tracing. To view traces:

1. Set up your Phoenix API key in the `.env` file
2. Run any example
3. View traces in the [Arize Phoenix dashboard](https://app.phoenix.arize.com/)

For local development, you can also run Phoenix locally:

```bash
docker run -p 6006:6006 arizephoenix/phoenix:latest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
