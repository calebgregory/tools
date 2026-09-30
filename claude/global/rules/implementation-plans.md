# Implementation plans

## The plan describes the current design; a changelog beside it holds the history

An implementation plan (`<name>.md`) states the design as it stands now: what we build, how the pieces
fit, what is decided and what is open. Status belongs in one place (a phase table or a status line at the
top), not sprinkled through the sections.

When a decision changes, edit the plan so it reads as if the new decision had always been the plan, and
record the change in `<name>.changelog.md` beside it: the date, what changed, what it replaced, who
decided and why, and which sections of the plan moved. Newest entry first. Withdrawn designs that are
worth keeping (a rejected API, an alternative someone may propose again) go in the changelog in full,
not in the plan "for the record".

Do not write "reversed on", "as first written", "kept for the record" or "since <date>" in the plan
itself. Those phrases mean history has leaked into the current-state document. A section may cite the
meeting or thread where a decision was made, since that is the source; it does not narrate how the
decision got there.

The rationale for a *current* decision stays in the plan, including the alternatives it rejected, because
a reader reviewing the design needs it. The story of decisions that no longer hold goes in the
changelog.

A document that a decision superseded (a handoff sent to someone, an earlier plan) gets a short header
saying so, pointing at what replaced it and which of its items still stand. Do not rewrite a document
someone has already received.

Create the changelog on the first change, not when the plan is written.
