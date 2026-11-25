## The user's guide preferences

These are Caleb's preferences for review guides. lemonaid appends this file to the packaged `review-guide` skill; `~/tools/lemons/lemonaid/bootstrap.py` links it to `~/.lemons/skills/review-guide/overlay.md`. Add an entry here when he states a new preference, then run `lemonaid skills install review-guide`.

- With each core change, show the unit tests that exercise it and show its behavior, in the same item, so I can read them together. Name the test functions and link them.
- Skip the guide for a round small enough to read in one sitting (a single hunk or a few lines in one file). Say what changed and where in chat instead, with `path:line` links.
