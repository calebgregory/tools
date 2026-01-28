import typing as ty
from pathlib import Path

from thds import humenc
from thds.core import config, hashing, project_root

_project_root = project_root._find_project_root(start=Path(__file__), anchor_file_name="pyproject.toml")
# ^ raises ValueError if project root not found
_WORKDIR_ROOT: ty.Final = _project_root / ".out"


def derive_workdir(input_file: Path, kind: str = "transcribe") -> Path:
    dirname = input_file.stem.replace(" ", "-")
    sha256_wordybin = humenc.encode(hashing.file("sha256", input_file))
    workdir = _WORKDIR_ROOT / kind / dirname / sha256_wordybin
    return workdir


workdir: config.ConfigItem[Path] = config.item("workdir", parse=Path, default=_WORKDIR_ROOT)
