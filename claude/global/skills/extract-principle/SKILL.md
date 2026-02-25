---
name: extract-principle
description: Distill a coding principle from corrections made during this conversation and add it to the appropriate rules file under ~/.claude/rules/.
disable-model-invocation: true
---

# Extract Principle

Analyze the current conversation to identify coding principles implied by the user's corrections to your output — either through direct edits, instructive feedback, or re-requests with different constraints.

## Steps

1. **Read existing rules** — read all `*.md` files under `~/.claude/rules/` to understand what's already documented and how it's structured
2. **Scan the conversation** for moments where the user corrected your output:
   - Direct instructions ("no, do it like X", "always use Y", "that's wrong because...", "why don't we do Z instead?")
   - Re-requests where the user rephrased with different constraints
   - Patterns where the user manually edited code you wrote (visible via file diffs or follow-up context)
3. **Distill the principle** — generalize from the specific correction to the underlying _why_. The principle should be:
   - **Abstract**: not tied to the specific file/variable/function from the correction
   - **Actionable**: tells Claude what to do (or not do) in future situations
   - **Concise**: follows the density and tone of existing rules (see style guide below)
4. **Check for duplication** — grep existing rules for related concepts. If a related rule exists:
   - Propose **amending** the existing rule rather than adding a new one
   - Show the before/after of the amendment
5. **Classify** — determine which existing file and section it belongs in, or whether it warrants a new file (explain why, propose a filename)
6. **Present the proposal** — show:
   - The correction(s) that motivated it
   - The proposed principle text
   - The target file and location (which section, or new section heading)
   - If amending: the diff of the existing rule
7. **Ask for confirmation** before writing anything
8. **Apply** — edit the target file on confirmation

## Style guide for principles

Match the voice and structure of the existing rules files:

- Start each principle with a `##` section heading that names the concept (imperative or noun-phrase)
- Follow with a short paragraph or bullet points explaining the principle
- Include a concrete example (code block with good/bad) only when the principle isn't obvious from prose alone
- Don't over-explain. Trust the reader to generalize.
- Don't restate what the heading already says in the first sentence.

## Rules

- Only extract principles that are **generalizable** — skip one-off preferences or project-specific decisions
- When in doubt about whether something is a principle vs. a one-off, ask the user
- Never write to rules files without explicit confirmation
- If the conversation contains multiple corrections, propose them one at a time
- If no corrections are found in the conversation, say so and exit — don't fabricate principles
