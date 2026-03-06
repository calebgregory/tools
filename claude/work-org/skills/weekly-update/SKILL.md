---
name: weekly-update
description: Generate a weekly update organized by project/workstream with progress notes, accomplishments, and next steps.
---

# Generate Weekly Update

Generate a weekly status update for the current Shape-up project. Posted in the project's Slack channel for PMs and ML Leadership.

## Audience

Product Managers and ML Leadership. They should understand what happened this week and what's coming next from this summary alone. They can consult the project task list for detailed progress context relative to the full pitch.

## Output Format

The update uses three sections — **Progress**, **Setbacks**, **Next Steps** — per the [guidebook](https://guidebook.trillianthealth.com/product-development/process/slack-for-ml-pitches/#weekly-status-updates).

```
**Week of YYYY-MM-DD — [Project Name]**

**Progress:**

- ✅ Accomplishment with enough detail to understand what was done
  - Sub-detail explaining *why* this matters or what it enables
  - 🔂 Caveat or provisional note
- ✅ Another accomplishment
  - 🏎️ Performance or efficiency callout
- 🫂 Meeting or collaboration point — what was decided

**Setbacks:**

- Obstacle encountered and its impact on scope or timeline
- Scope reductions with justification
- (or "None" if a clean week)

**Next steps:**

- Upcoming work with context for why it's prioritized
- What's the focus for next week
```

## Output File

Write to `projects/<project>/weekly-updates/YYYY-MM-DD.md` where the date is the **Monday of the week** (week start), not the day the update is generated.

## Emoji Markers

Use emojis as visual markers for scanning:

- ✅ completed item
- 🔂 provisional, caveated, or "will need to revisit" item
- 🏎️ performance or efficiency callout
- 🫂 meeting, collaboration, or people-oriented item

## Steps

1. **Get current project context**:
   - Read `current-project.md` for project name, Slack channel, and branch names
   - Read the project's task list (follow `[see](...)` refs from `todo/todo.md`) — this is the pitch's Task List that readers can reference for full scope

2. **Gather week's work**:
   - Read daily notes for the week: `daily/{YYYY}/{YYYY-MM-DD}.md` for Monday through today
     - Use `## Completed` for tasks finished each day
     - Use `## Summary` and `## Outline` for context and narrative
   - Git log for additional context:
     `git -C <monorepo> log --oneline --since="YYYY-MM-DD 00:00" --author="<name from ~/.gitconfig>" <branch>`
   - Look for patterns: what themes emerge from the work?

3. **Draft the update**:
   - **Progress**: Describe completed work precisely — what was built, what was learned, what decisions were made. Reference Task List items where applicable.
   - **Setbacks**: Surface bad news quickly. Explain obstacles and their impact on scope. Identify items falling behind. Describe scope reductions with justification. If none, say "None."
   - **Next steps**: Outline upcoming work with reasoning for prioritization.

4. **Synthesize, don't list**:
   - Group related commits/tasks into coherent accomplishments
   - "Built X which does Y" is better than listing 5 commits
   - Link to PRs or Slack threads when they add context
   - Organize by impact, not chronology

5. **Explain why, not just what**:
   - Sub-bullets should give context for someone unfamiliar with the implementation
   - "Built X" -> sub-bullet explains what X does and why it's needed in the pipeline
   - Don't assume the reader knows internal data structures — briefly explain domain-specific concepts when first introduced

6. **Technical terms**: Always backtick-wrap domain-specific identifiers, table names, column names, and code artifacts (e.g., `id_overrides`, `source_patient_id`, `trilliant`-tokens)

7. **Blank lines after section headers** — separate `**Progress:**` from the first bullet with a blank line for readability

8. **Output the formatted update** ready to copy-paste into the project Slack channel

## Content Sources

| Source | What to extract |
|--------|-----------------|
| Daily notes | Completed tasks, summaries, narrative context |
| Git log | Commits grouped by feature (context, not enumerated) |
| Project todo file | Task List items — completed this week and upcoming |
| Todo.md | Open tasks, blockers, follow-ups |
| current-project.md | Project name, Slack channel, branch names |

## Rules

- Focus on the current project — this is a project status update, not a personal activity report
- Organize by impact, not chronology
- Be precise about what was built or decided, not vague "made progress" statements
- One PR = one bullet (with sub-details if needed), not one bullet per commit
- Include links to significant PRs and Slack threads
- If cooldown week, note that and adjust structure accordingly
