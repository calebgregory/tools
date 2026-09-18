---
name: end-of-pitch-report
description: Draft an end-of-pitch report for tech leadership — what was promised, what shipped, what was cut, and what comes next, per the Trilliant guidebook.
argument-hint: [executive|technical|both]
---

# End-of-Pitch Report

Draft the end-of-pitch report for the current Shape-up project, following the [guidebook guidelines](https://guidebook.trillianthealth.com/product-development/process/writing-guidelines/#end-of-pitch-reports).

## Purpose

An honest, concise account for tech leadership of what was built, what changed, and what comes next — written to **inform future decisions, not to summarize effort**.

## Audience & tone

The target reader is a tech lead who did **not** work the pitch. They should read it in **5–10 minutes** and understand what happened. Concise and reflective, outcome-focused — never effort-focused.

## Arguments

`$ARGUMENTS` selects the variant:

- _(none)_ or `executive` — the leadership-facing report (default). This **is** the guidebook report.
- `technical` — the implementation-facing companion (see below). Only meaningful alongside an executive report.
- `both` — produce the executive report, then the technical companion that extends it.

When unsure which is wanted, produce the executive report and offer the technical companion.

## Executive vs. technical — how they relate

These are **not** two reports at different detail levels. They have different jobs and a strict relationship:

- **Executive** is the report the guidebook describes — the six required sections below, for a tech lead who did not work the pitch. It is the complete, standalone account of _what_ shipped, _what_ was cut, and _what_ comes next, written to inform decisions. Most readers only read this.
- **Technical** is a pure **extension** of the executive, for a future _implementer_. It opens by stating it assumes the executive and **does not restate what shipped or why** — it adds only the implementation decisions, gotchas, design notes, and PR-level internals that a person continuing the work would otherwise have to reconstruct. Its sections **key to the executive's deliverables** (one section per deliverable that has depth worth recording); it does _not_ re-run the six guidebook sections.

The test for a technical bullet: if it restates a fact already in the executive, cut it. If it's something you'd have to dig out of a PR diff or a design doc to act on the work, keep it. Sourcing the technical report therefore means reading the **PR descriptions and diffs** and the **project's own design / implementation-plan docs**, not the daily notes:

- `gh pr view <n> --json title,body,state,files` for each PR named in the executive.
- The project's design docs (e.g. `projects/<project>/src/**/implementation-plans/*.md`, `redaction/research/*.md`) for settled methodology, rejected alternatives, and open questions.

## Required sections (executive)

Per the guidebook, the executive report must address all six:

1. **What was promised** — brief restatement of the Solution's commitments (from the pitch).
2. **What shipped** — actual deliverables, explained at a level accessible to non-implementers.
3. **What was cut** — scope that didn't make it, **with reasons**. Do not omit this.
4. **Challenges that affect future work** — technical debt, unexpected constraints, failed approaches.
5. **Immediate follow-up** — work required as a direct result of what shipped.
6. **The bigger picture** — potential future directions, what more time would enable, open questions.

A "bottom line" closing paragraph (as in the cycle-14 executive report) is a good optional addition.

## Format

- Include **evidence**: summary statistics for data work (fill rates, compute-time deltas, cohort/patient counts, row counts), and screenshots/video for app changes.
- Link to merged PRs, Slack threads, and READMEs that add context.
- Backtick-wrap domain identifiers, table/column names, and code artifacts.

## Steps

1. **Get project context**:
   - Read `current-project.md` for project name, Slack channel, project dir, and branches.
   - Read the project's **pitch document** (under `ml-collab/pitches/<cycle>/...` or `product-dev/pitches/<cycle>/`) for the original Solution commitments, Rabbit Holes, and No-Gos — section 1 ("What was promised") restates these.
   - Read the project's **implementation plan** (`projects/<project>/src/implementation-plan.md`) and **task list** (the Slack list and/or `projects/**/todo.md` or `checklist.md` files) for per-task status — these drive "what shipped" vs. "what was cut".

2. **Reconcile status** — if it exists, the Slack task list is the source of truth for what's Done / Downhill / Uphill / Deferred. Cut scope = items marked deferred/cut or never started; shipped = Done; in-flight = anything still uphill/downhill at pitch end (note these honestly under follow-up).

3. **Gather the cycle's narrative**:
   - Daily notes across the cycle: `daily/{YYYY}/{YYYY-MM-DD}.md` (`## Completed`, `## Summary`, `## Outline`).
   - Git log on the project branch for the cycle window:
     `git -C <monorepo> log --oneline --since="<cycle-start>" --author="<name from ~/.gitconfig>" <branch>`
   - Pull quantitative evidence where the work produced metrics.

4. **Draft the executive report**, each section in the order above. Synthesize — group related commits/tasks into coherent deliverables ("Built X which does Y"), organize by impact not chronology.

5. **Reflect before finalizing** — the guidebook calls out "writing without adequate reflection time" as a common failure. The bigger-picture and challenges sections need genuine reflection, not a task-list paraphrase.

6. **If producing the technical companion**, do it _after_ the executive is settled (it extends a moving target otherwise). Read the PR descriptions/diffs and project design docs (see "Executive vs. technical" above), then write one section per executive deliverable that has implementation depth — decisions, gotchas, design notes — and nothing that merely restates the executive. Open with the "assumes the executive; does not restate" framing.

## Output file

Preferred layout — a directory holding both:

- `projects/<project>/src/end-of-pitch/executive.md`
- `projects/<project>/src/end-of-pitch/technical.md` (links back to `./executive.md`)

For an executive-only report, a single `projects/<project>/end-of-pitch-report.md` is fine.

## Common mistakes to avoid

- Summarizing **effort** instead of **outcomes**.
- Describing **future work** as if it were completed work.
- **Omitting scope cuts** (section 3 is mandatory).
- **Vague follow-up** — every follow-up item needs a specific next action, not "continue work on X".
- Writing without adequate **reflection time**.
- **Technical report that restates the executive** — if a technical bullet repeats what/why instead of adding implementation depth, cut it. The technical report extends; it does not duplicate at higher resolution.
