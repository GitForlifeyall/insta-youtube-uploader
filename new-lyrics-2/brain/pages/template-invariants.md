---
id: template-invariants
title: Existing template visual styles are protected invariants
category: decision
status: active
tags: [templates, visual-safety]
created: "2026-09-16T00:32:38"
updated: "2026-09-16T00:32:54"
---

<!-- compiled_truth -->
## Current understanding

Template 1, Template 2, Template 3, Brat Minimal, and YT Hindi Type are distinct product aesthetics. Their default visual styles are protected invariants. An agent may inspect, explain, test, or fix a defect in a template, but must not modify, rewrite, remove, or restyle a template unless the user explicitly requests a change to that specific template.

## Practical consequence

When a task could touch template rendering, first identify the template key and ask for explicit authorization if the proposed edit changes its default visual result. Feature work that is isolated from a template may proceed normally.

## Related context

- [[yt-hindi-type-contract]]
- [[agent-safety-and-scope]]


## Timeline

- time: 2026-09-16T00:32:38
  kind: decision
  summary: "Created this page: Existing template visual styles are protected invariants"
  source: AGENTS.md and repository inspection
  affects: [template-invariants]

- time: 2026-09-16T00:32:54
  kind: decision
  summary: Recorded the explicit user requirement to protect all existing template styles.
  source: AGENTS.md and repository inspection
  affects: [template-invariants]
