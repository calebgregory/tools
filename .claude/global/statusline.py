#!/usr/bin/env python3
"""Claude Code statusline command - displays contextual info in the terminal."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Colors matching xonsh prompt
ORANGE = "\033[38;5;214m"  # #ffaf00
CYAN = "\033[38;5;80m"  # #5dd8c8
BLUE = "\033[1;34m"  # bold blue
PURPLE = "\033[1;35m"  # bold purple
RED = "\033[31m"  # red for elapsed time
RESET = "\033[0m"

CLAUDE_DIR = Path.home() / ".claude"
LAST_MESSAGE_TIME_DIR = CLAUDE_DIR / "last-message-time"


def get_session_timestamp_file(data: dict) -> Path | None:
    """Get the session-specific timestamp file path."""
    session_id = data.get("session_id")
    if session_id:
        return LAST_MESSAGE_TIME_DIR / f"{session_id}.txt"
    return None


def get_git_branch(cwd: str) -> str:
    """Get current git branch, or empty string if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode != 0:
            return ""

        result = subprocess.run(
            ["git", "-C", cwd, "--no-optional-locks", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        branch = result.stdout.strip()
        return f" {branch}" if branch else ""
    except (subprocess.TimeoutExpired, Exception):
        return ""


def get_elapsed_since_last_message(timestamp_file: Path | None) -> str:
    """Read the previous timestamp and return formatted elapsed time."""
    if timestamp_file is None:
        return ""
    try:
        if timestamp_file.exists():
            prev_timestamp = float(timestamp_file.read_text().strip())
            elapsed = time.time() - prev_timestamp
            if elapsed >= 0:
                return f"{RED}{elapsed:.1f}s{RESET}"
    except (ValueError, OSError):
        pass
    return ""


def write_current_timestamp(timestamp_file: Path | None) -> None:
    """Write current timestamp to the session-specific file."""
    if timestamp_file is None:
        return
    try:
        timestamp_file.parent.mkdir(parents=True, exist_ok=True)
        timestamp_file.write_text(str(time.time()))
    except OSError:
        pass  # Silently fail if we can't write


def calculate_context_percentage(data: dict) -> str:
    """Calculate context window usage percentage."""
    usage = data.get("context_window", {}).get("current_usage")
    if not usage:
        return ""

    current = (
        usage.get("input_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
        + usage.get("cache_read_input_tokens", 0)
    )
    size = data.get("context_window", {}).get("context_window_size", 0)

    if size > 0:
        pct = current * 100 // size
        return f" {pct}%"
    return ""


def get_vim_indicator(vim_mode: str) -> str:
    """Build vim mode indicator."""
    if not vim_mode:
        return ""
    if vim_mode == "NORMAL":
        return " [N]"
    return " [I]"


def render_statusline(data: dict) -> None:
    """Render the statusline to stdout."""
    # Extract values from JSON
    cwd = data.get("workspace", {}).get("current_dir", "")
    vim_mode = data.get("vim", {}).get("mode", "")

    # Get short cwd (basename)
    short_cwd = os.path.basename(cwd) if cwd else ""

    # Get git branch
    branch = get_git_branch(cwd) if cwd else ""

    # Get current time
    current_time = time.strftime("%H:%M:%S")

    # Get elapsed time since last message (session-specific)
    timestamp_file = get_session_timestamp_file(data)
    elapsed = get_elapsed_since_last_message(timestamp_file)

    # Calculate context window usage
    context_pct = calculate_context_percentage(data)

    # Build vim mode indicator
    vim_indicator = get_vim_indicator(vim_mode)

    # Build elapsed part (with space prefix if present)
    elapsed_part = f" {elapsed}" if elapsed else ""

    # Build and print status line
    # Format: <time elapsed> short_cwd branch context_pct vim_mode
    print(
        f"{ORANGE}<{current_time}{elapsed_part}>{RESET} "
        f"{BLUE}{short_cwd}{RESET}"
        f"{CYAN}{branch}{RESET}"
        f"{context_pct}"
        f"{vim_indicator}",
        end="",
    )


def main() -> None:
    # Check for command-line mode
    if len(sys.argv) > 1 and sys.argv[1] == "write-last-message-time":
        # Hook mode: just write the timestamp and exit
        # (JSON from stdin provides session_id and project_dir for the file path)
        data = json.load(sys.stdin)
        timestamp_file = get_session_timestamp_file(data)
        write_current_timestamp(timestamp_file)
    else:
        # Default mode: render the statusline
        data = json.load(sys.stdin)
        render_statusline(data)


if __name__ == "__main__":
    main()
