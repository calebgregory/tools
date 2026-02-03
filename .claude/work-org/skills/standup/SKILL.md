---
name: standup
description: Generate a daily standup update from recent work — "previous workday | current workday" format with nested bullets and links.
argument-hint: [tomorrow]
---

# Generate Standup Update

Generate a daily standup update based on recent tasks, commits, and voice memos.

## Output Format

```
# Standup — YYYY-MM-DD HH:MMam/pm

**Yesterday (YYYY-MM-DD):**

\`\`\`
- completed task or work item
    - detail or context
    - PR #123 merged ([link](<github-url>))
- another item
\`\`\`

**Today (YYYY-MM-DD):**

\`\`\`
- planned task
    - subtask or detail
- follow up on X ([thread](<slack-url>))
\`\`\`
```

## Formatting Rules (for DailyBot compatibility)

1. **4-space indentation** for nested bullets (DailyBot requires this for proper nesting)
2. **Links in trailing parentheses**: `([thread](<url>))` or `([link](<url>))`
   - Keeps URLs out of the main text
   - Avoids issues with `->` in text being parsed as link closers
3. **Wrap each section's bullet list in triple backticks** to preserve indentation in editor
4. The H1 header is a generation timestamp: `# Standup — YYYY-MM-DD HH:MMam/pm`
5. Section headers include the date: `**Yesterday (YYYY-MM-DD):**`

## Arguments

- `tomorrow` — Shift perspective for end-of-day prep: treat today as "yesterday" and tomorrow as "today". Useful for preparing tomorrow's standup the night before.

## Output File

- **Default**: Write to `todo/today.md`
- **`tomorrow` arg**: Write to `todo/tomorrow.md`

## Steps

1. **Determine timeframe**:
   - **Default**: yesterday = previous workday (Friday if Monday), today = today
   - **`tomorrow` arg**: yesterday = today, today = next workday (Monday if Friday)

2. **Gather "yesterday" content**:
   - Read `todo/_archive/` for the previous workday's completed tasks
   - Run `git -C <monorepo> log --oneline --since="<prev-day> 00:00" --until="<prev-day> 23:59" --author="<user>"`
   - Check `<project-dir>/cc/notes/` (via `current-project.md`) for transcripts from previous day
   - Read todo.md for any tasks marked complete that haven't been archived yet

3. **Gather "today" content**:
   - Read todo.md for open tasks, especially those with `{due: today}` or no due date
   - Check for `{status: awaiting ...}` items that need follow-up
   - Note any blockers or dependencies

4. **Format the update**:
   - Group related items together
   - Include links to PRs, Slack threads as trailing parentheticals: `([link](<url>))`
   - Keep bullets concise — details go in sub-bullets
   - Use past tense for yesterday, future/present for today
   - Use 4-space indentation for nesting
   - Wrap each section in triple backticks

5. **Write the standup** to `todo/today.md` (or `todo/tomorrow.md` if `tomorrow` arg)

## Content Priority

**Yesterday (what to include):**

- Completed tasks with meaningful work (not trivial checkboxes)
- PRs merged or reviewed
- Key discussions or decisions from Slack
- Blockers resolved

**Today (what to include):**

- High-priority open tasks
- Items with deadlines
- Follow-ups on yesterday's work
- Meetings or syncs if mentioned

## Rules

- Keep it scannable — managers skim these
- Link to artifacts (PRs, threads) when they add context
- Don't pad with trivial items
- If nothing significant happened, say so briefly
- Match the team's typical level of detail
