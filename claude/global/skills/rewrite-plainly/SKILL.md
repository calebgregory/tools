---
name: rewrite-plainly
description: Apply the Reader-facing prose and Writing-in-my-voice guidance to an existing document. Invoke with /rewrite-plainly [file-path].
---

Rewrite an existing document to conform to the "Reader-facing prose" and "Writing in my voice" sections of CLAUDE.md.

## Step 1: Determine the target

The user may provide a file path as an argument, or describe the document verbally.

- **If a file path is provided:** Read it.
- **If no path is provided:** Ask what document to rewrite. It could be a file on disk, a scratch file, a
  draft in the conversation, or an Obsidian note (fetch via `obsidian-api`).

## Step 2: Classify the document

Determine which rules apply:

- **Reader-facing prose** (the anti-patterns checklist, register, and structure rules) applies to all
  documents.- **Writing in my voice** (contractions, first person, casual register) applies only if the document will
  read as the user's own writing. Ask if it's not obvious from context. Technical reference docs, ADRs, and shared explainers typically should NOT use his personal voice. Proposals, Slack messages, pitch updates, and Obsidian notes typically should.

## Step 3: Audit

Before rewriting, scan the document and list the specific violations you found, grouped by type.
Present them to the user as a short summary, for example:

> Found 3 contrastive pairs, 2 setup/payoff openers, 1 buried lede, and several instances of dense
> vocabulary. The structure leads with background instead of conclusions. No voice-matching issues
> (document is a reference doc, not written in your name).

Ask: **"Want me to rewrite, or do you want to adjust what I'm targeting?"**

## Step 4: Rewrite

Apply the fixes. Do not change the factual content, technical accuracy, or organizational structure of the
document unless the structure rule ("lead with conclusions") specifically calls for reordering. The goal is
to change how the document says things, not what it says.

Preserve:

- All factual claims, data, numbers, and technical details
- Section headings (unless they are themselves anti-pattern violations like setup/payoff labels)
- Tables, code blocks, and structured data verbatim
- Links and references
- Document-level metadata (frontmatter, tags)

## Step 5: Present the result

Show the rewritten document. If the document is short enough, show it inline. If it's long, write it to
the scratchpad directory and tell the user where to find it.

Do not write the result back to the original location without explicit approval. If the original is an
Obsidian note or Relay document, remind the user of the relevant write constraints (obsidian-api for
vault notes, relay-api for Relay notes, and the Relay REST server must be enabled).
