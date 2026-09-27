# ⚡ Small Tasks Policy: Delegate to Codex

> **Mandatory Rule:** If any task is a **small task**, it must **always be delegated to Codex**.

---

## 🎯 What Counts as a "Small Task"?

Always assign the following types of tasks directly to **Codex**:

1. **Single-File Tweaks & Route Adjustments**:
   - Modifying a single function or route in FastAPI / Express.
   - Adding a query parameter, header, or payload field.
   - Adjusting CSS classes, inline styles, layout padding, or colors.

2. **Quick Bug Fixes & Edge Cases**:
   - Fixing a typo, syntax error, or unclosed session/resource leak.
   - Correcting regular expressions, regex parsing, or string splits.
   - Handling a specific status code or error response gracefully.

3. **Standalone Helpers & Scrapers**:
   - Writing self-contained scrapers or utility functions (e.g. `public_scrapers.py`, `best_times.py`, `competitor_spy.py`).
   - Creating isolated scripts or CLI testing utilities.

4. **Documentation & Config Updates**:
   - Updating markdown guides, `.env` templates, or comments.
   - Creating task specs inside `.codex/tasks/TASK_XX.md`.

5. **Isolated Unit / Component Tests**:
   - Adding a test script to verify an API endpoint or helper function.

---

## 🛠️ How to Delegate to Codex

1. **Task Spec File**: Create a dedicated spec file in `.codex/tasks/TASK_XX_<NAME>.md` describing:
   - Target file(s).
   - Expected inputs and outputs.
   - Verification command.
2. **Execute via Codex**: Hand off the task directly to Codex to write the code surgically and verify it.
3. **Review & Merge**: Confirm the automated test passes and mark the task completed.

---

## 🛑 What Should NOT Go to Codex?

Large architectural tasks remain with the primary planning agent:
- Full system refactors spanning multiple microservices.
- Designing new database schemas or major architectural migrations.
- Designing entirely new subsystems or end-to-end authentication protocols.
