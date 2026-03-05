# Visibility

## Log destructive and state-changing actions

When code silently overwrites, deletes, or replaces existing state (files, database rows, cached artifacts), log enough context that a future investigator — human or agent — can reconstruct what happened. A warning-level log before a destructive action is cheap insurance against invisible data loss.
