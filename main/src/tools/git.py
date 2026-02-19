import subprocess
from functools import lru_cache
from pathlib import Path


@lru_cache
def repo_root(file: Path | None = None) -> Path:
    cwd = (file if file.is_dir() else file.parent) if file and file.exists() else None
    return Path(
        subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True, cwd=cwd).strip()
    )
