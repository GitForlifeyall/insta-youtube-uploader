# 🤖 Codex Task Delegation Directive

> **Rule:** If any task is a **small task**, it must be delegated to **Codex**.

---

## 📌 1. Core Policy

Whenever a user or workflow requires a task to be executed, check its scope:

- **Small Task** $\rightarrow$ **Give to Codex** (Delegate directly to Codex agent / queue in `.codex/tasks/`).
- **Complex / Architectural Task** $\rightarrow$ Handled by Lead Architect / Antigravity with full planning.

---

## 🔍 2. What Qualifies as a "Small Task"?

Any task matching any of the following criteria must be delegated to **Codex**:

1. **Single-File Modifications:**
   - Editing a function, adjusting a route, or updating an endpoint.
   - Tweaking CSS styles, UI colors, padding, or DOM selectors.
   - Modifying environment variables, configs, or `.env` entries.

2. **Quick Bug Fixes & Patches:**
   - Fixing syntax errors, typos, missing imports, or unhandled exceptions.
   - Resolving port collisions, path formatting issues, or encoding bugs.
   - Updating package scripts or dependencies.

3. **Standalone Scripts & Utilities:**
   - Writing one-off test scripts, scratch runners, or helper tools.
   - Creating simple CLI wrappers or alias files.

4. **Documentation & Formatting:**
   - Updating README files, docstrings, comments, or markdown guides.
   - Formatting JSON, YAML, or Markdown files.

5. **Unit / Component Tests:**
   - Writing isolated test cases for an existing service or module.

---

## ⚙️ 3. Execution Workflow for Codex

When a small task is assigned:

1. **Task Definition:** Create or log the task in [`.codex/tasks/`](file:///.codex/tasks/) if tracking via files, or delegate directly using the Codex execution runner / subagent.
2. **Targeted Edit:** Codex must make concise, minimal, surgical edits without refactoring surrounding unrelated code.
3. **Verification:** Codex must verify that the fix works cleanly without introducing regressions.
4. **Handoff:** Report completion back with the exact files modified and verification results.

---

## 🛑 4. What Does NOT Go to Codex?

Large architectural tasks remain with the primary planning agent:
- Full system refactors spanning multiple microservices.
- Designing new database schemas or major architectural migrations.
- Designing entirely new subsystems or end-to-end authentication protocols.
