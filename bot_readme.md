# LLM Composition Patterns - High-Level Summary

## Project Overview

This codebase demonstrates various LLM composition patterns for data processing and transformation. Each pattern represents a different approach to orchestrating LLM interactions for specific tasks, with practical examples using a fictional outdoor apparel brand (KETL Mtn. Apparel) as the theme.

## Core Patterns

The project showcases five main composition patterns, each implemented as a separate module:

1. **Prompt Chaining**: Sequential processing where the output of one LLM call becomes the input for the next
2. **Routing**: Directing inputs to specialized handlers based on query classification
3. **Parallelization**: Distributing tasks across multiple concurrent LLM calls
4. **Orchestrator-Workers**: Using a central LLM to coordinate specialized worker LLMs
5. **Evaluator-Optimizer**: Iterative refinement through feedback loops

## Project Structure

```
src/llm_composition_patterns/
├── common/                          # Shared utilities and data
│   ├── groq_helpers.py              # Groq API integration
│   ├── fireworks_helpers.py         # Fireworks API integration
│   ├── message_types.py             # Common message structures
│   ├── arize_phoenix_setup.py       # Observability setup
│   └── ketlmtn_data/                # Example data for demonstrations
├── patterns/                        # Implementation of each pattern
│   ├── prompt_chaining/             # Pattern 1
│   │   ├── README.md                # Pattern documentation
│   │   └── example.py               # Implementation example
│   ├── routing/                     # Pattern 2
│   │   ├── README.md
│   │   └── example.py
│   ├── parallelization/             # Pattern 3
│   │   ├── README.md
│   │   └── example.py
│   ├── orchestrator_workers/        # Pattern 4
│   │   ├── README.md
│   │   └── example.py
│   └── evaluator_optimizer/         # Pattern 5
│       ├── README.md
│       └── example.py
└── __init__.py
```

## Pattern Implementation Details

Each pattern follows a consistent implementation approach:

- **README.md**: Documents the pattern with:
  - Overview and concept explanation
  - Implementation details with specific examples
  - Key components and features
  - Usage examples with code snippets
  - Benefits and limitations

- **example.py**: Demonstrates the pattern with:
  - Practical implementation using the KETL Mtn. context
  - Type hints and documentation following Python standards
  - Integration with LLM providers (Groq, Fireworks)
  - Observability via Arize Phoenix tracing

## Common Components

The codebase uses several shared utilities:

- **LLM Provider Helpers**: Wrappers for Groq and Fireworks APIs with async support
- **Message Types**: Standardized structures for LLM interactions
- **Example Data**: Product and company information for the KETL Mtn. examples
- **Tracing**: Integration with Arize Phoenix for observability

## Frontend Design Requirements

To create a frontend similar to agentrecipes.com but with mountain earth tones:

1. **Homepage Layout**:
   - Header with project title and brief description
   - Cards for each pattern with visual diagrams
   - Consistent use of mountain earth tones (forest greens, stone grays, bark browns)

2. **Pattern Pages**:
   - Clear pattern description and use cases
   - Interactive diagrams showing data flow
   - Code examples with tabbed interface showing different files
   - "Copy code" functionality

3. **Workflow Tags**:
   - Tag patterns with relevant characteristics (e.g., "Workflow", "Low latency", "Loops")
   - Use consistent styling for tags across the site

4. **Navigation**:
   - Simple top navigation
   - Clear path back to pattern overview

5. **Code Presentation**:
   - Syntax highlighting
   - Tabs to switch between related files (example.py, helpers, etc.)
   - Comments explaining key concepts

## Frontend-Backend Sync Strategy

To ensure the frontend properly represents the backend code:

1. Extract pattern descriptions and examples directly from README.md files
2. Generate diagrams based on the actual data flow in example.py files
3. Show both high-level explanations and technical implementation details
4. Include real code snippets with proper syntax highlighting
5. Ensure documentation reflects actual implementation behavior

This structure will allow users to understand both the conceptual patterns and their practical implementation, similar to the agentrecipes.com approach but tailored to your specific LLM composition patterns. 