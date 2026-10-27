---
name: meeting-summary
description: Correct transcription errors in a meeting transcript and write a summary file alongside it.
argument-hint: [transcript-path | YYYY-MM-DD]
---

# Meeting Summary

Two passes over a meeting transcript: fix known mishearings in place, then write a summary file next to it. Either pass can run alone — if the transcript is already corrected, skip to the summary.

## Arguments

- Transcript path: use that file
- `YYYY-MM-DD`: find the transcript for that date under the current project's `meetings/` directory
- No argument: use the most recently modified transcript in the current project's `meetings/` directory, and say which one you picked before editing it

Find the project directory from `current-project.md`.

## Source and destination

- Source: `<project>/src/meetings/{YYYY-MM-DD}.{slug}.md`
- Destination: `<project>/src/meetings/{YYYY-MM-DD}.{slug}.summary.md`

Transcripts are speaker-labelled markdown: `**Speaker Name**: text`, one blank line between turns. Interjections interleave mid-sentence, so a single speaker's thought often spans several non-adjacent turns.

If the transcript lives under `ml-collab` or `product-dev`, run `obsidian-open <path>` before editing it (see the repo CLAUDE.md).

## Pass 1 — Correct the transcript

### 1. Load the corrections table

Read `memory/transcription-corrections.md` from the project memory directory. It maps misheard text to the correct term, with contextual qualifiers in the left column ("Kate's (in compute/infra context)").

### 2. Read the whole transcript

Read it in chunks until you have all of it. You cannot spot a mishearing without the surrounding conversation — most entries in the table are only wrong in one context.

### 3. Build the replacement list, then apply it in one script

Write a Python script to the scratchpad with a list of `(old, new)` exact-phrase pairs, and have it assert each `old` appears exactly once:

```python
missing = []
for old, new in pairs:
    n = s.count(old)
    if n != 1:
        missing.append((old, n))
        continue
    s = s.replace(old, new)
print("UNMATCHED:", missing)
```

Report anything unmatched instead of silently skipping it. Do not hand-edit dozens of sites — a scripted pass with a match assertion is how you know every intended fix landed and nothing extra did.

Include enough surrounding words in each `old` to make it unique and to keep it away from text that must not change. Speaker labels are the main hazard: replacing `Berthe` with `birth` would corrupt every `**Cheick Berthe**` speaker label, so match `volume of Berthe records` instead.

Use regex only for global normalizations that are safe everywhere in the file — capitalizing a company or product name, for example — and print the substitution count for each so the user can sanity-check it.

### 4. Correct the raw transcript, not just the summary

Fix mistranslations inline in the transcript text. The transcript records what people said, not what the transcriber heard.

### 5. Flag garble; don't guess

Some turns are genuinely unrecoverable — a stray word, a half-sentence, a name that fits nothing in context. List those for the user with the speaker and the surrounding context, and leave the text alone. A plausible-sounding guess in a transcript is worse than visible noise, because the reader can't tell it was invented.

Corrections you are confident about but that aren't in the table yet (a garbled term whose meaning the surrounding conversation makes obvious) go in, and get reported in the summary of what you changed.

### 6. Update the corrections table

Append the new mishearings you found to `memory/transcription-corrections.md`. Write the left column with a contextual qualifier whenever the same misheard text would be correct elsewhere. If a correction you made in an earlier pass turns out to be wrong, edit that row rather than adding a second one.

## Pass 2 — Write the summary

### 1. Pick the format

- **Standalone**: all topics in one file, one `##` section each.
- **Topic hub**: a short intro, then a numbered list of topics where each entry links to its own `{YYYY-MM-DD}.{slug}.{topic}.md` file and carries a one-sentence gist. Write those topic files as part of this pass — they don't need to exist beforehand.

Complexity decides. Split into topic files when the sync covered several substantial, largely independent threads — each with its own decisions, numbers, and follow-ups — such that a single file would run long enough that a reader looking for one thread has to scan past the others. Two or three related topics stay in one file; six threads spanning different teams and releases are easier to read and easier to link to as separate files. `projects/cycle-17-intake-pipeline-837-xf-testing/src/meetings/2026-08-19.sync.summary.md` is the worked example of the hub format.

Say which format you chose and why before writing, so the user can redirect you cheaply.

When splitting:

- The hub carries the framing paragraph, the topic list, cross-cutting notes, and the consolidated action items. Keep the per-topic follow-ups in their topic file too, so each file stands alone.
- Each topic file gets its own heading, a link back to the transcript, and the same reader-facing treatment as a standalone summary.
- Name topic files by subject, not by number: `2026-08-19.sync.dd-issues-review.md`, not `...topic-3.md`. Numbering breaks when a topic gets added or dropped.

### 2. Structure

```markdown
# {YYYY-MM-DD} {Meeting name} — Summary

**Attendees:** {names, from the speaker labels}

**Transcript:** [{filename}]({filename})

{One paragraph: what this meeting was for and how it broke down.}

## {Topic heading}

{Prose and bullets.}

## Action items

- [ ] **{Owner}:** {what they committed to}
```

Derive attendees from the speaker labels — never from the calendar or from who was expected.

Link any artifact referenced during the meeting (diagrams, checklists, pitch documents) with a relative path.

If you think there is relevant code under discussion, either find or ask for it.  With an absolute path
to the file, you can find the current commit hash and the remote url for the git repository and craft a
github URL to the file(s) being discussed.

### 3. What to capture

- Lead each section with the decision or outcome, then the reasoning that got there.
- Keep the numbers people cited — record counts, sizes, dates, dollar figures. They are the reason someone rereads a summary.
- Separate what was decided from what is still open. When nobody decided, say so plainly rather than implying consensus.
- Attribute positions to people when they disagreed, and give both sides.
- Name the follow-up owner and the deadline where one was stated.
- Note staffing and availability that affects the schedule (leave, PTO, coverage).
- Give a topic its own `##` section when it has its own decision or follow-up; fold one-liners into a closing "Other items raised" section.

### 4. Write it as reader-facing prose

The writing-style rules for reader-facing prose apply. In particular:

- Active voice with the agent named — "We drop the delay", not "the delay is dropped".
- Introduce every reference from scratch. The reader wasn't in the meeting and hasn't read the transcript.
- Conclusions first. No "In this meeting we discussed...".

## Report

Tell the user:

- Which transcript you corrected, and the fixes grouped by kind (names and data sources, domain terms, misc)
- What you left alone as unrecoverable, with the speaker and context
- Which rows you added to the corrections table
- Where the summary landed, and which format you used
- Any action item from the meeting that isn't in `todo/todo.md` yet — offer to add it, don't add it unprompted

## Rules

- Never guess at unrecoverable speech.
- Never delete or rewrite content in the transcript beyond correcting mishearings. Filler, false starts, and crosstalk stay.
- Apply the scripted-with-assertions approach for any correction pass over about five sites.
- Don't write a summary from a partial read of the transcript.
