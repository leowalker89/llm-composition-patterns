# Workflow Diagrams

This directory contains Mermaid diagram source files for the different LLM workflow patterns.

## Rendering Diagrams

These .mmd files can be rendered using:
- The Mermaid CLI: `mmdc -i filename.mmd -o filename.png`
- Online Mermaid Live Editor: https://mermaid.live
- VS Code with the Mermaid extension

## Diagram Types

- `prompt_chaining.mmd`: Sequential LLM calls where each processes the output of the previous
- `routing.mmd`: Classification and routing to specialized LLM handlers
- `parallelization.mmd`: Breaking tasks into independent subtasks run in parallel
- `orchestrator_workers.mmd`: Central LLM delegating to worker LLMs
- `evaluator_optimizer.mmd`: One LLM generates while another evaluates in a feedback loop