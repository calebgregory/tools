---
name: apply-update
description: Process a voice memo transcript to update tasks — mark completed ones for archiving, add new ones, update statuses.
argument-hint: <transcript filename, e.g., 26-02-02_1700_end-of-day-recap>
---

# Apply Update from Voice Memo

Process a voice memo transcript to update the todo list.

## Steps

1. **Locate the transcript**:
   - Search all `**/cc/notes/` directories in the project root for transcripts
   - If `$ARGUMENTS` provided, find matching file across all cc/notes locations
   - If no extension given, append `.md`
   - If file not found or no arguments, list available transcripts from all locations and ask which one
2. **Parse the transcript** for task-related content:
   - **Completed tasks**: Things mentioned as done/finished/completed
   - **New tasks**: Things mentioned as needing to be done, follow-ups
   - **Status updates**: Blockers, waiting-on, progress notes
   - **Context/details**: Additional info about tasks useful for standup/weekly reports
3. **Match completed items to todo.md and archive**:
   - Fuzzy match descriptions against open `[ ]` tasks in todo.md
   - Also check `todo/_archive/` for already-completed tasks (skip these)
   - Consider subtasks (memo might reference a subtask specifically)
   - If ambiguous match, show options and ask
4. **Prepare changes**:
   - Mark matched tasks as `[x]`
   - Add new tasks with normalized due dates
   - Update status tags where mentioned
   - Add relevant context as sub-bullets to tasks (in todo.md or `_archive/`)
5. **Present summary** of proposed changes before applying:
   ```
   ## Proposed Changes

   ### To complete (will archive)
   - "end of week report" → matches "- [ ] end of week report..."

   ### To add
   - [ ] follow up with Fincher on CI fix {due: 2026-02-03}

   ### Status updates
   - "review PRs" → add {status: awaiting CI fix}

   ### Context to add
   - "cycle 13 PR" → add sub-bullet: "addressed Joe's feedback on error handling"
   ```
6. **On confirmation**:
   - Apply changes to todo.md
   - Add context sub-bullets to archived tasks in `_archive/` if relevant
   - Run archive-completed logic for newly completed tasks
7. **Confirm** what was done

## Matching Heuristics

- Case-insensitive partial matching
- "Finished the PR review" → matches tasks containing "PR review"
- "Got the weekly report posted" → matches "end of week report"
- Keywords: "done", "finished", "completed", "wrapped up", "submitted", "merged"

## New Task Detection

Look for phrases like:
- "Need to...", "Should...", "Have to...", "Don't forget to..."
- "Tomorrow I'll...", "Next I need to..."
- "Blocked on...", "Waiting for..."

Extract due dates by running `~/tools/relative_dates.py` and using matching keys (`tomorrow`, `monday`, `end_of_week`, etc.).

## Context Worth Capturing

Add as sub-bullets to tasks (useful for standup/weekly reports):
- What specifically was done: "addressed feedback on error handling"
- Decisions made: "went with approach B after discussing with Joe"
- Blockers encountered/resolved: "CI was failing due to flaky test"
- Collaborators involved: "paired with Fincher on the fix"
- Links mentioned: PR URLs, Slack threads

## Rules

- Always show proposed changes before applying
- For ambiguous matches, ask rather than guess
- Preserve context from the transcript in archived tasks
- Don't duplicate tasks already in todo.md or archived in `todo/_archive/`
- Normalize all due dates to YYYY-MM-DD format when adding

If no `$ARGUMENTS` are provided, list recent transcripts from all `**/cc/notes/` directories and ask which to process.
