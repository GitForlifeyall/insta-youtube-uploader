# Calendar

## Mission
Create implementation-ready, token-driven UI guidance for Calendar that is optimized for consistency, accessibility, and fast delivery across dashboard web app.

## Brand
- Product/brand: Calendar
- URL: https://app.metricool.com/planner/calendar?blogId=4191302&userId=3291677
- Audience: authenticated users and operators
- Product surface: dashboard web app

## Style Foundations
- Visual style: structured, tokenized, content-first
- Main font style: `font.family.primary=Nunito Sans`, `font.family.stack=Nunito Sans, webfontregular, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif, Apple Color Emoji, Segoe UI Emoji, system-ui`, `font.size.base=16px`, `font.weight.base=400`, `font.lineHeight.base=24px`
- Typography scale: `font.size.xs=11px`, `font.size.sm=12px`, `font.size.md=14px`, `font.size.lg=14.72px`, `font.size.xl=16px`, `font.size.2xl=18px`, `font.size.3xl=20px`
- Color palette: `color.surface.base=#000000`, `color.text.secondary=#ffffff`, `color.text.tertiary=#1e2326`, `color.text.inverse=#13232f`, `color.surface.raised=#e7ff56`, `color.border.strong=#2d1a29`, `color.border.default=#edf2f7`, `color.border.muted=rgb(235, 238, 239) rgb(0, 0, 0) rgb(0, 0, 0) rgb(235, 238, 239)`
- Spacing scale: `space.1=2px`, `space.2=3px`, `space.3=4px`, `space.4=6px`, `space.5=8px`, `space.6=12px`, `space.7=16px`, `space.8=24px`
- Radius/shadow/motion tokens: `radius.xs=8px`, `radius.sm=12px`, `radius.md=16px`, `radius.lg=50px`, `radius.xl=100px` | `shadow.1=rgba(0, 0, 0, 0.08) 0px 0px 0px 0px, rgba(0, 0, 0, 0.05) 0px 0px 0px 0px, rgba(0, 0, 0, 0.03) 0px 0px 0px 0px`, `shadow.2=rgba(0, 0, 0, 0.1) 0px 0px 6px 1px` | `motion.duration.instant=150ms`, `motion.duration.fast=200ms`, `motion.duration.normal=280ms`, `motion.duration.slow=500ms`

## Accessibility
- Target: WCAG 2.2 AA
- Keyboard-first interactions required.
- Focus-visible rules required.
- Contrast constraints required.

## Writing Tone
Concise, confident, implementation-focused.

## Rules: Do
- Use semantic tokens, not raw hex values, in component guidance.
- Every component must define states for default, hover, focus-visible, active, disabled, loading, and error.
- Component behavior should specify responsive and edge-case handling.
- Interactive components must document keyboard, pointer, and touch behavior.
- Accessibility acceptance criteria must be testable in implementation.

## Rules: Don't
- Do not allow low-contrast text or hidden focus indicators.
- Do not introduce one-off spacing or typography exceptions.
- Do not use ambiguous labels or non-descriptive actions.
- Do not ship component guidance without explicit state rules.

## Guideline Authoring Workflow
1. Restate design intent in one sentence.
2. Define foundations and semantic tokens.
3. Define component anatomy, variants, interactions, and state behavior.
4. Add accessibility acceptance criteria with pass/fail checks.
5. Add anti-patterns, migration notes, and edge-case handling.
6. End with a QA checklist.

## Required Output Structure
- Context and goals.
- Design tokens and foundations.
- Component-level rules (anatomy, variants, states, responsive behavior).
- Accessibility requirements and testable acceptance criteria.
- Content and tone standards with examples.
- Anti-patterns and prohibited implementations.
- QA checklist.

## Component Rule Expectations
- Include keyboard, pointer, and touch behavior.
- Include spacing and typography token requirements.
- Include long-content, overflow, and empty-state handling.
- Include known page component density: buttons (136), cards (52), links (15), inputs (5), tables (4), navigation (1).


## Quality Gates
- Every non-negotiable rule must use "must".
- Every recommendation should use "should".
- Every accessibility rule must be testable in implementation.
- Teams should prefer system consistency over local visual exceptions.
