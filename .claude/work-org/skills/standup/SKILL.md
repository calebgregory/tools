---
name: standup
description: Generate a daily standup update from recent work — "previous workday | current workday" format with nested bullets and links.
argument-hint: [tomorrow]
---

# Generate Standup Update

Generate a daily standup update based on daily notes and open tasks.

## Output Format

```
# Standup — YYYY-MM-DD HH:MMam/pm

**Yesterday (YYYY-MM-DD):**

\`\`\`
- workstream or project name
    - met with X; decided to do Y
    - narrative about what happened and why
    - PR review remediation
- support things
    - investigated X for Y reason
\`\`\`

**Today (YYYY-MM-DD):**

\`\`\`
- main goal for the day, with context
- support
    - follow up on X
    - context about status or blockers
- get around to trying Z
- maybe more work on W if time permits
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

1. **Determine timeframe** using the shared script (do not guess weekdays):
   ```bash
   ~/tools/relative_dates.py
   ```
   - **Default**: yesterday = `prev_workday`, today = `today`
   - **`tomorrow` arg**: yesterday = `today`, today = `next_workday`

2. **Gather "yesterday" content**:
   - **Read the daily note**: `daily/{YYYY}/{YYYY-MM-DD}.md` for the previous workday
     - Use the Summary and Outline sections for narrative
     - Use the Completed section for specific tasks finished
     - Use Transcripts for additional context if needed
   - Read todo.md for any tasks marked complete that haven't been archived yet
   - Git log as background context only (don't enumerate commits):
     `git -C <monorepo> log --oneline --since="<prev-day> 00:00" --until="<prev-day> 23:59" --author="<user>"`

3. **Gather "today" content**:
   - Check if daily note exists for today (`daily/{YYYY}/{YYYY-MM-DD}.md`) — use its outline for planned work
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

- **Use the daily note's Summary and Outline** — these are already in a good narrative format
- **Use the Completed section** for specific tasks that were finished
- Meetings and decisions first — "met with X; out of that meeting, we decided to..."
- Narrative about what happened and *why*, not just what code changed
- Group by workstream/project, not flat list of tasks
- PRs as context, not the main event
- Blockers resolved

**Today (what to include):**

- Main goal with context ("deploy X after finishing Y, then solicit feedback")
- Follow-ups with status context ("I reviewed X and had questions about Y")
- Softer commitments for lower-priority items ("get around to", "maybe more")
- Avoid pure checkbox lists — show intent

## Rules

- **Don't enumerate commits** — summarize the work narratively
- Group by workstream/project (current project, support, etc.)
- Keep it scannable — managers skim these
- Link to artifacts (PRs, threads) when they add context
- If nothing significant happened, say so briefly
- Use conversational sub-bullets when context helps ("we're very nearly done with that")
