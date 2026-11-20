#!/usr/bin/env -S uv run python
"""Install our additions to lemonaid's home, then render the lemonaid skills they change."""

import sys

from lemons import lemonaid

if __name__ == "__main__":
    sys.exit(lemonaid.install())
