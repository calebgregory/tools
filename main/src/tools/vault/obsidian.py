import shutil
import subprocess
from pathlib import Path


def obsidian_open(p: Path) -> bool:
    """wraps a utility on my PATH for opening a file in obsidian"""
    if shutil.which("obsidian-open"):
        try:
            subprocess.check_call(["obsidian-open", p])
            return True
        except subprocess.CalledProcessError:
            pass
    return False
