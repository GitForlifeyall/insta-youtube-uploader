---
name: save-decision
description: Saves a durable LyricalVideo requirement, constraint, technical decision, or creator workflow rule using the brain.md CLI. Use after a decision that will matter in six months.
---

# Save durable knowledge

First decide whether this belongs in the brain. It does only if it is difficult to reconstruct from code and will still affect work in six months.

Do not save routine edits, chat transcripts, media inventories, raw lyrics, credentials, or short-lived debugging notes.

If the decision is new:

```powershell
npx --yes @mindmux/brain-md create-page --id <kebab-id> --category decision --title "<title>" --tags <comma-separated-tags> --source "creator decision"
```

Then save the current understanding through the CLI:

```powershell
@'
## Current understanding

<decision, reason, alternatives, impact, and links to related pages>
'@ | npx --yes @mindmux/brain-md update-truth --id <kebab-id> --summary "<one-line summary>" --source "creator decision"
```

If the decision already exists, use `update-truth` and append a reversal timeline item if the old conclusion changed. Run `npx --yes @mindmux/brain-md lint-links` after adding wiki-links.
