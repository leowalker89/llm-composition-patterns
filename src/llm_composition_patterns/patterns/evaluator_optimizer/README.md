# Evaluator-Optimizer Pattern

## Overview

The Evaluator-Optimizer pattern implements an iterative improvement cycle where content is repeatedly generated, evaluated, and refined based on feedback. This pattern is ideal for creating high-quality outputs that must meet specific criteria.

## How It Works

1. **Generation**: Create an initial piece of content
2. **Evaluation**: Assess the content against predefined criteria
3. **Optimization**: Use the evaluation feedback to improve the content
4. **Repeat**: Continue this cycle until the content meets all criteria or reaches a maximum iteration limit

## Implementation Details

This example demonstrates the pattern by generating and refining sales pitches for KETL Mtn. Apparel products. The implementation:

- Uses a more powerful model (`llama-3.1-8b-instant`) for both content generation and evaluation to ensure high-quality results
- Employs Pydantic models for robust data validation and structured responses
- Separates system and user prompts for clearer responsibility boundaries
- Includes comprehensive tracing with OpenTelemetry and Arize Phoenix for observability

## Key Components

### Pydantic Models
- `ProductData`: Structure for product information with validation
- `EvaluationCriteria`: Individual evaluation criteria with score and feedback
- `EvaluationResult`: Complete evaluation output with overall pass/fail status

### Generation Stage
- `generate_sales_pitch()`: Creates a sales pitch based on product data and optionally incorporates feedback from previous evaluations
- Uses product information and brand voice guidelines to generate contextually appropriate content
- Wrapped in tracing span with relevant attributes

### Evaluation Stage
- `evaluate_sales_pitch()`: Assesses the pitch against multiple criteria including brand voice, technical accuracy, and persuasiveness
- Returns structured feedback as a Pydantic model for reliable parsing and validation
- Uses error handling with fallbacks for robust processing
- Wrapped in tracing span with pitch length and product attributes

### Optimization Loop
- The `optimize_sales_pitch()` function orchestrates the generate-evaluate-optimize loop
- Continues until either the evaluation passes or maximum iterations are reached
- Tracks progress and stores iteration history
- Wrapped in tracing span with product and iteration limit attributes

## Tracing and Observability

This implementation includes OpenTelemetry tracing with Arize Phoenix integration:
- All key functions are instrumented with spans
- Spans include useful attributes like product ID, pitch length, and iteration counts
- The trace hierarchy clearly represents the iteration cycles
- Main workflow is captured in a parent span with child spans for each step

This enables comprehensive monitoring and analysis of the pattern's performance and effectiveness.

## Usage

Run the example with a specific product ID:

```bash
python -m llm_composition_patterns.patterns.evaluator_optimizer.example 5
```

Default settings:
- Product ID: 5 (Shenanigan Outdoor Pants)
- Maximum iterations: 3

## Why This Pattern Matters

The Evaluator-Optimizer pattern is particularly valuable when:

- Quality standards are high and non-negotiable
- The first attempt at content creation is unlikely to be perfect
- Specific, measurable criteria must be met
- There's value in documenting the improvement process

For content publishing workflows where quality is crucial, the additional compute cost of multiple iterations is justified by the higher quality of the final output.
