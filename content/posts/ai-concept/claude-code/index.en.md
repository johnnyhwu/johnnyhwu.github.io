---
# weight: 1
title: "Claude Code Concepts: Agentic Loop, Tools, Skills, and Permissions"
date: 2026-07-24
lastmod: 2026-07-24
draft: false
description: "A concept-level tour of Claude Code's architecture: the read-think-act agentic loop, its tool system, CLAUDE.md project memory, hooks, skills, MCP, and permission model."
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Single-Agent", "Agent Memory"]
categories: ["ai-concept"]
# series: ["getting-start"]
# series_weight: 1

url: "ai-concept/:contentbasename"
---

<!--more-->

## Introduction

*   **Not an autocomplete tool.** Claude Code is Anthropic's agentic coding CLI: instead of suggesting the next line while a human drives, it is handed a goal, and it drives — reading files, running commands, editing code, and checking its own work in a loop, autonomously.
*   **A concrete instance of the "Model + Harness + Context" framework.** The [harness engineering](../harness-engineering/) view of agents — frozen model, execution harness, dynamically assembled context — isn't just theory here; Claude Code's tool system, hooks, and `CLAUDE.md` memory are a working implementation of exactly that split.
*   **Goal of this note:** walk through Claude Code's core mechanisms — the agentic loop, tools, extensibility (skills, hooks, MCP), context management, and the permission model that keeps an autonomous coding agent safe to run unattended.

## What Claude Code Actually Is

Claude Code runs as a CLI (and SDK) process that wraps a single core primitive: an LLM that can call tools, observe the results, and decide what to do next — repeatedly, until it judges the task done. There is no separate "planner module" or "executor module" bolted on top; planning and execution both happen inside the same loop, driven by the model's own reasoning about what it just observed.

This distinguishes it from IDE autocomplete (which predicts tokens, not actions) and from earlier "chat about your code" assistants (which only read, but couldn't act). Claude Code's defining trait is that **observation and action are the same substrate**: a failed test's stderr becomes the next prompt's input without a human relaying it.

## The Agentic Loop

At its core, the loop is simple to state and hard to get right in production:

```python
def agent_loop(user_task, tools, cwd):
    context = load_project_memory(cwd)      # CLAUDE.md, prior turns
    transcript = [user_task]

    while not done:
        response = model.call(transcript, context, tool_schemas=tools)

        if response.is_final_answer:
            done = True
            continue

        # Every tool call is a chance for the harness to intervene
        if requires_confirmation(response.tool_call):
            approved = ask_user(response.tool_call)
            if not approved:
                transcript.append(denial_feedback(response.tool_call))
                continue

        result = execute(response.tool_call, cwd)
        transcript.append(observation(response.tool_call, result))
```

Two properties matter more than the loop's shape:

*   **Every turn is inspectable.** Because the model must emit an explicit tool call rather than a free-text "I will now edit the file," the harness gets a clean interception point — for permission checks, for logging, for hooks — before anything actually happens.
*   **Failure is just another observation.** A failing test, a syntax error, a denied permission — none of these terminate the loop. They become the next input, and the model re-plans around them. This is the same "throw it back on the wheel" idea from the [Ralph Loop](../harness-engineering/#ralph-loop-the-orchestrator): a monolithic loop that recovers from errors is more robust than a brittle multi-stage pipeline that doesn't expect them.

## The Tool System

Claude Code's action space is a small set of general-purpose tools rather than hundreds of task-specific ones — deliberately, so the model can compose them instead of hunting for the "right" narrow tool:

| Tool | Role |
| :--- | :--- |
| `Read` / `Glob` / `Grep` | Understand the codebase — read a known file, find files by pattern, search content by regex — without loading everything into context. |
| `Edit` / `Write` | Make targeted changes (`Edit` does exact string replacement; `Write` is for new files or full rewrites). |
| `Bash` | Run arbitrary shell commands — build, test, lint, install, git — the general escape hatch for anything the dedicated tools don't cover. |
| `Task` (subagents) | Delegate a self-contained piece of work to a separate agent instance with its own context window, returning only a summary. |
| `WebFetch` / `WebSearch` | Pull in information outside the local filesystem when the codebase alone doesn't answer the question. |

The important design choice isn't any single tool — it's that dedicated, narrow tools (`Read`, `Edit`, `Grep`) are offered *and preferred* over the general-purpose `Bash` escape hatch wherever one fits. A narrow tool has a smaller failure surface than shelling out to `sed`/`cat`, and its structured output is easier for both the model and the harness to reason about.

## Extending the Agent: Skills, Hooks, and MCP

A frozen model plus a fixed tool list would be too rigid for the range of tasks a coding agent actually meets. Claude Code's harness layer adds three extension points, each solving a different problem:

### Skills — packaged, discoverable procedures

A skill is a directory of instructions (and optionally scripts) describing how to do a specific, recurring task — this site's own `hugo-paper-post` skill, which turns a paper's notes into a bilingual blog post, is one example. Skills are only loaded into context on demand: the model sees a one-line description of each available skill up front, and pulls in the full instructions only for the one it actually needs. This is the same **progressive disclosure** principle covered in the harness-engineering note's [Just-In-Time tool injection](../harness-engineering/#just-in-time-jit-tool-injection) — don't pay the context cost for capabilities the current task doesn't use.

### Hooks — deterministic control at lifecycle events

Hooks are shell commands the harness runs at fixed points — before a tool executes, after the agent finishes responding, when a session starts. Because a hook is ordinary code, not a model call, it's the right place for guarantees the model itself can't be trusted to enforce reliably: blocking a write to a protected path, auto-formatting a file after every edit, or failing a turn outright if a lint check doesn't pass. Hooks are how "the agent should never do X" becomes an enforced rule instead of a hopeful instruction in a system prompt.

### MCP — a standard protocol for external tools

The Model Context Protocol lets Claude Code talk to external services — a GitHub server, a database, an internal API — through a common interface, instead of each integration needing bespoke, hand-rolled tool code. An MCP server declares its own tools and resources; the harness surfaces them to the model the same way it surfaces built-in tools. This is what lets one agent reach a Slack workspace, a ticket tracker, and a private repo without the harness author writing a client for each.

## Context Engineering in Practice

Claude Code is also a working example of the ideas in the [context engineering](../context-engineering/) note — a stateless model made to feel stateful through careful context assembly.

*   **`CLAUDE.md` as project-level memory.** A checked-in `CLAUDE.md` file — like the one governing this very repository's blog-publishing conventions — is read at the start of a session and folded into context automatically. It plays the role of the harness-engineering note's "Org-level" memory tier: durable, shared, and independent of any single conversation.
*   **Context compaction.** Long sessions eventually approach the context window's limit. Rather than truncating blindly, Claude Code summarizes older turns into a compact digest and keeps working — the conversation continues without the user needing to restart or re-explain earlier decisions.
*   **Subagents as context isolation.** Dispatching a broad, exploratory search (e.g., "find everywhere a config value is used across a large codebase") to a subagent via the `Task` tool keeps that search's noisy intermediate output out of the main loop's context — only the subagent's final summary comes back. This is the "Folding" pattern from the context-engineering note in practice: complex sub-work produces a sawtooth in context length instead of a permanent, ever-growing tax on the main conversation.

{{< admonition tip "Why this matters in practice" >}}
None of these three mechanisms individually is novel — summarization, scoped delegation, and project config files all predate agentic coding tools. What makes them a "harness," not just features, is that they compose automatically: a subagent's summary can itself get folded into a later compaction pass, and `CLAUDE.md` conventions apply consistently whether the current turn came from the user or from a hook-triggered retry.
{{< /admonition >}}

## The Permission Model and Blast Radius

An agent that can run arbitrary shell commands and edit files unattended needs a safety layer that doesn't depend on the model always guessing correctly. Claude Code's approach is graduated rather than binary:

*   **Permission modes** range from asking before every non-trivial action, to auto-approving a defined allowlist (e.g., read-only commands, or edits within the working directory), to fully autonomous execution in an isolated environment — the user picks the mode, not the model.
*   **Reversibility drives what gets a confirmation prompt.** Reading a file or running a test is auto-approved almost everywhere, because it's cheap to be wrong about. Force-pushing, deleting branches, or `rm -rf` sit behind an explicit confirmation by default in every mode, because undoing them after the fact may not be possible.
*   **Sandboxing bounds the worst case.** Even with a permissive mode, running in a container or a scoped environment means a bad shell command can't reach outside the task's own working directory — the permission model and the execution boundary are two independent layers, not one substituting for the other.

This mirrors the sandboxing and rollback discussion in the harness-engineering note's [Git-based state & sandboxes](../harness-engineering/#git-based-state--sandboxes) section: the goal isn't to make the agent incapable of mistakes, it's to make mistakes cheap and reversible so the loop can keep running instead of needing a human to intervene on every misstep.

## Where Claude Code Sits in the Agent-Harness Landscape

Compared to [OpenClaw](../openclaw-intro/)'s emphasis on long-running autonomy and self-directed tool-making, Claude Code is deliberately narrower in scope: it is optimized for the software-engineering loop specifically — read code, change code, verify the change — with skills, hooks, and MCP as the mechanism for extending that loop into adjacent tasks (writing this very blog post included), rather than for open-ended general autonomy. The trade-off is intentional: a narrower, well-instrumented action space is easier to make both capable and safe than a fully general one.

## Conclusion

Claude Code is best understood not as "a chatbot with file access" but as a small, composable harness around a frozen model: a tight agentic loop, a deliberately narrow tool system, three extension points (skills, hooks, MCP) for adding capability without bloating the base context, and a permission model that scales confirmation friction to how reversible an action actually is. None of the individual pieces are exotic — what makes it work is that they're designed to compose, so that a session started days ago, a project's own conventions, and a one-off delegated subtask all feed back into the same loop cleanly.
