# D-023 — GUI-First Local Development Workflow

- **Status:** Accepted
- **Date accepted:** 2026-10-27

## Context

The PO prefers VS Code UI and one-click recurring tasks to repetitive terminal commands.

## Decision

- Prefer VS Code's supported graphical UI, including C# Dev Kit, Solution Explorer, NuGet package management and Tasks, for routine development actions.
- Use direct shell commands for initial setup, troubleshooting, or when no suitable GUI action exists.
- Once build/test checks recur, provide a small repository-managed entry point such as a VS Code Task or `checkAll`; do not add tooling solely for the initial JSON prototype.
- During guided setup, provide one actionable stage per turn and wait for the PO's result. Existing automated unit tests and PO acceptance requirements remain unchanged.

## Consequences

Provide repeatable development actions without premature tooling or terminal repetition.
