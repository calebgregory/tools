---
name: weekly-update
description: Generate a weekly update organized by project/workstream with progress notes, accomplishments, and next steps.
---

# Generate Weekly Update

Generate a project-focused weekly update summarizing progress across workstreams.

## Output Format

```
**Week of YYYY-MM-DD**

## [Current Project Name]
- accomplishment or progress point
  - detail, link to [PR](url) or [thread](url)
- another accomplishment
- **Next:** upcoming work or focus

## Support / Other
- support ticket or ad-hoc item
- review or collaboration work

## Blockers / Notes
- any blockers or things to flag
```

## Steps

1. **Get current project context**:
   - Read `current-project.md` for project name and Slack channel
   - This becomes the primary section header

2. **Gather week's accomplishments**:
   - Read `todo/_archive/` for all entries from this week (Monday through today)
   - Run `git -C <monorepo> log --oneline --since="last monday" --author="<user>"`
   - Check `<project-dir>/cc/notes/` for all transcripts this week
   - Look for patterns: what themes emerge from the work?

3. **Organize by workstream**:
   - **Current project**: Main Shape-up project work
   - **Support / Other**: Support rotation, reviews, ad-hoc requests
   - **Blockers / Notes**: Anything to flag for the team

4. **Synthesize, don't list**:
   - Group related commits/tasks into coherent accomplishments
   - "Implemented X" is better than listing 5 commits
   - Link to the PR that represents the work, not individual commits

5. **Add forward-looking notes**:
   - What's the focus for next week?
   - Any deadlines or milestones coming up?

6. **Output the formatted update** ready to copy-paste

## Content Sources

| Source | What to extract |
|--------|-----------------|
| Archive | Completed tasks with context |
| Git log | Commits grouped by feature/PR |
| Transcripts | Key decisions, context, quotes |
| Todo.md | Upcoming work for "next" section |
| current-project.md | Project name, channel |

## Rules

- Organize by impact, not chronology
- One PR = one bullet (with sub-details if needed), not one bullet per commit
- Include links to significant PRs and Slack threads
- Keep support/other section brief unless it was a heavy support week
- If cooldown week, note that and adjust structure accordingly
- Match your team's weekly update conventions
