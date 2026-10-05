# Isaac — AI Code Provenance

## Purpose

Document how AI coding systems were used without representing them as independent owners of the Isaac project.

## Development model

AI systems were used as engineering tools for:

- implementation
- test creation
- debugging
- refactoring
- documentation
- code review / analysis

The project owner remained responsible for:

- product concept
- theoretical foundation
- architecture
- requirements
- system boundaries
- governance model
- goals and priorities
- acceptance criteria
- deciding which generated changes were retained
- runtime validation and integration

## Agent/tool families used

The project history contains work associated with, among others:

- Google Jules
- GitHub Copilot
- Codex
- Claude
- other coding assistants as used during development

Per-commit attribution should be treated as an engineering provenance signal, not as an ownership statement.

## Human-controlled architecture

The repository's `AGENTS.md` establishes the repository as the operative architectural authority and defines strict boundaries between Registry, Strategy and Executor. It also states that the AI model is a tool for execution rather than the authoritative source of architecture or system logic.

## Validation

Generated or AI-assisted changes are accepted only through project-controlled processes such as:

- tests
- regression checks
- smoke tests
- runtime verification
- code review
- Git history
- architectural constraints

## Security

Do not place the following into this document:

- API keys
- OAuth tokens
- passwords
- private prompts containing secrets
- authentication exports
- private customer data

## Acquisition diligence note

A buyer should receive the provenance policy and relevant Git history, but not private account credentials or unrelated personal conversation data.
