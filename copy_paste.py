import subprocess
import typing as ty


def _do(cmd: ty.List[str]) -> str:
    """returns the output of the process as a str"""
    return subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].rstrip().decode("utf-8")


def pbpaste() -> str:
    return _do(["pbpaste"])


def pbcopy(text_to_copy: str) -> None:
    process = subprocess.Popen("pbcopy", env={"LANG": "en_US.UTF-8"}, stdin=subprocess.PIPE)
    process.communicate(text_to_copy.encode("utf-8"))
