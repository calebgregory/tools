#!/usr/bin/env -S uv run python
"""Install Codex adapters and shared context."""

from lemons.bootstrap import bootstrap

if __name__ == "__main__":
    bootstrap("codex")
