---
name: standup
description: Generate a daily standup update from recent work — "previous workday | current workday" format with nested bullets and links.
argument-hint: [tomorrow]
---

# Generate Standup Update

Generate a daily standup update based on recent tasks, commits, and voice memos.

## Output Format

```
**Previous workday | Today**

**Yesterday:**
- completed task or work item
  - detail or context
  - [PR #123](github-url) merged
- another item

**Today:**
- planned task
  - subtask or detail
- [thread](slack-url) follow up on X
```

## Arguments

- `tomorrow` — Shift perspective for end-of-day prep: treat today as "yesterday" and tomorrow as "today". Useful for preparing tomorrow's standup the night before.

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
   - Include links to PRs, Slack threads where relevant
   - Keep bullets concise — details go in sub-bullets
   - Use past tense for yesterday, future/present for today

5. **Output the formatted standup** ready to copy-paste

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
