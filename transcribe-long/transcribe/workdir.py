from pathlib import Path

from thds.core import hashing


def derive_workdir(input_file: Path, root_dirname=".transcribe") -> Path:
    dirname = input_file.stem.replace(" ", "-")
    sha256 = str(hashing.file("sha256", input_file), encoding="utf-8")
    workdir = Path(f"{root_dirname}/{dirname}/{sha256}")
    return workdir
