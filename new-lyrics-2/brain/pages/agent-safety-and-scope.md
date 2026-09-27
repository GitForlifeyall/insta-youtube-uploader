---
id: agent-safety-and-scope
title: "Agent boundaries for code, media, credentials, and destructive actions"
category: project
status: active
tags: [agents, safety, antigravity]
created: "2026-09-16T00:32:49"
updated: "2026-09-16T00:33:04"
---

<!-- compiled_truth -->
## Current understanding

Agents may read relevant project files, propose plans, run bounded diagnostics, and make explicitly requested implementation changes. They must not edit `.env`, expose credentials, or scan source media without a task-specific reason. They must ask before deletion, recursive moves, overwrites of meaningful files, package installation, history-rewriting Git operations, external uploads, or any change that alters a protected template's default appearance.

## Antigravity operating mode

Use workspace-local rules and skills. Start in review/approval mode. Keep outside-workspace access disabled unless the creator deliberately opens the separate creator vault. Use narrow file scope and avoid autonomous cleanup instructions.

## Related context

- [[template-invariants]]
- [[render-safety-contract]]


## Timeline

- time: 2026-09-16T00:32:49
  kind: decision
  summary: "Created this page: Agent boundaries for code, media, credentials, and destructive actions"
  source: AGENTS.md and repository inspection
  affects: [agent-safety-and-scope]

- time: 2026-09-16T00:33:04
  kind: decision
  summary: Recorded mandatory safeguards for Antigravity and other coding agents.
  source: AGENTS.md and repository inspection
  affects: [agent-safety-and-scope]
