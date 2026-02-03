---
name: add
description: Add a work task to the todo list. Use when capturing new work items, PRs to review, or follow-ups.
argument-hint: <task description> [thread](url) {due:...} {status:...}
disable-model-invocation: true
---

# Add Task

Add a task to the work todo file.

## Steps

1. Parse the argument: extract task description, any inline links `[text](url)`, and metadata tags `{due:...}`, `{status:...}`
2. Normalize due dates to concrete format (see Date Normalization below)
3. Read the todo file (see Environment in CLAUDE.md)
4. Determine placement:
   - If the task is clearly a subtask of an existing open item (contextually related), indent under that parent
   - Otherwise append to the end of the file
5. Add the line: `- [ ] <task description> <links> <tags>`
6. Write the file
7. Confirm with the single line you added

## Date Normalization

When writing tasks, convert relative dates to concrete YYYY-MM-DD format:
- `today` → `2026-02-02` (today's date)
- `tomorrow` → `2026-02-03`
- `end of week` → `2026-02-07` (Friday)
- `end of day tomorrow` → `2026-02-03`
- `this week` → `2026-02-07`

Preserve time qualifiers after the date: `{due: today by noon}` → `{due: 2026-02-02 by noon}`

This makes tasks precise — no one has to do mental math later.

## Examples

`/add review Fincher's PR [PR](https://github.com/org/repo/pull/123) {due: today}`
→ Appends: `- [ ] review Fincher's PR [PR](https://github.com/org/repo/pull/123) {due: 2026-02-02}`

`/add follow up on data quality thread [thread](https://slack.com/...) {status: awaiting response}`
→ Appends with status tag (no due date to normalize)

`/add check pinned items {due: end of morning tomorrow}`
→ Appends: `- [ ] check pinned items {due: 2026-02-03 end of morning}`

## Rules

- Normalize all relative dates to YYYY-MM-DD format
- Include all links provided by the user
- If adding as a subtask, use tab indentation to match existing structure
- Don't add area tags — this is work-focused, not multi-area like the personal vault

If no `$ARGUMENTS` are provided, ask what task to add.
