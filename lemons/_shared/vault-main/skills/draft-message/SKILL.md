---
name: draft-message
description: Draft an outreach message (email, text, call script) for any life area. Two versions — warm and concise.
argument-hint: <recipient and context, e.g., "Barnes exterminators, schedule inspection">
---

# Draft Message

Draft a message to someone — email, text, or call talking points.

## Steps

1. Parse `$ARGUMENTS` for recipient name and purpose/context
2. Check `todo/contact.md` for any info about this person
3. Scan todo files for tasks mentioning this person or related context
4. Determine message type from context:
   - **Email** — include subject line options
   - **Text** — keep short, casual
   - **Call script** — bullet points for talking points
   - If unclear, default to email format
5. Draft two versions:
   - **Version A (warm)** — friendly, personal tone
   - **Version B (concise)** — short, direct, gets to the point
6. Present both versions in the conversation

## Output format

```
# Message Draft: [Recipient] — [Purpose]

**Subject line options:** (if email)
1. ...
2. ...

## Version A (warm)
[Full message]

## Version B (concise)
[Full message]

## Notes
[Any relevant context: relationship, sensitivities, follow-up timing]
```

## Rules

- Don't save to a file — just present in the conversation for copy/paste
- Match the tone to the relationship (contractor ≠ friend ≠ community member)
- If there's a task related to this person, reference the specific ask from the task
- Keep texts under 3 sentences for Version B
- For call scripts, use bullet points not full paragraphs

If no `$ARGUMENTS` are provided, ask who the message is for and what it's about.
