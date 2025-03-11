# Agentic Systems Showcase

A practical demonstration of LLM workflow patterns and agent architectures inspired by Anthropic's "Building Effective Agents" article.

## Overview

This project provides interactive examples and implementations of the various workflow patterns and agent architectures described in Anthropic's engineering blog post ["Building Effective Agents"](https://www.anthropic.com/engineering-at-anthropic/building-effective-agents) (December 2024). The showcase aims to help developers understand and implement these patterns in their own applications.

Rather than relying on complex frameworks, this project demonstrates simple, composable patterns that have proven effective in production environments across various industries.

## Included Patterns

### Building Block: The Augmented LLM

The foundation of all agentic systems - an LLM enhanced with:
- Retrieval capabilities
- Tool usage
- Memory

### Workflow Patterns

#### Prompt Chaining
Decomposing tasks into sequential steps, where each LLM call processes the output of the previous one.
- Best for tasks with clear, fixed subtasks
- Trades latency for higher accuracy

#### Routing
Classifying input and directing it to specialized followup tasks.
- Enables separation of concerns and specialized prompts
- Ideal for handling distinct categories of inputs

#### Parallelization
- **Sectioning**: Breaking tasks into independent subtasks run in parallel
- **Voting**: Running the same task multiple times for diverse outputs
- Best when subtasks can be run concurrently or multiple perspectives are needed

#### Orchestrator-Workers
A central LLM dynamically breaks down tasks, delegates to worker LLMs, and synthesizes results.
- Well-suited for complex tasks with unpredictable subtasks
- Provides more flexibility than fixed parallelization

#### Evaluator-Optimizer
One LLM generates a response while another provides evaluation and feedback in a loop.
- Effective with clear evaluation criteria
- Valuable for iterative refinement processes

### Autonomous Agents

Full agent implementations that:
- Understand complex inputs
- Engage in reasoning and planning
- Use tools reliably
- Recover from errors
- Operate independently with human checkpoints

## Implementation Philosophy

Following Anthropic's recommendations, this project emphasizes:
1. **Simplicity** in design
2. **Transparency** in showing planning steps
3. **Well-crafted interfaces** through thorough tool documentation

## Getting Started

(Instructions for setup, installation, and running examples will be provided here)

## Contributing

(Contribution guidelines will be provided here)

## License

(License information will be provided here)

## Acknowledgements

This project is inspired by and based on Anthropic's research and engineering insights shared in their article ["Building Effective Agents"](https://www.anthropic.com/engineering-at-anthropic/building-effective-agents) by Erik Schluntz and Barry Zhang.
