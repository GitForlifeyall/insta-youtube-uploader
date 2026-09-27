# Project Brain protocol

Always read `@/BRAIN.md` after `AGENTS.md` at the start of a meaningful task.

Use the project brain to retrieve only durable context relevant to the task. The CLI is available through:

```powershell
npx --yes @mindmux/brain-md list-pages
npx --yes @mindmux/brain-md read-root <slug>
npx --yes @mindmux/brain-md read-page <id>
```

Never manually edit files under `brain/`. Use the brain CLI for every brain write.

Write to the brain only when a requirement, architecture choice, safety constraint, reusable troubleshooting insight, or creative-production rule will matter in six months and cannot be recovered easily from code. Do not record routine implementation detail.

At the end of a meaningful task, either state that no durable knowledge changed or invoke `/save-decision` with the new insight.
