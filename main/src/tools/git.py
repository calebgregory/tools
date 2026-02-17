import subprocess
from functools import lru_cache
from pathlib import Path


@lru_cache
def repo_root() -> Path:
    return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
