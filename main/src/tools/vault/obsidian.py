import shutil
import subprocess
import typing as ty
from pathlib import Path


def _list_vault_names() -> list[str]:
    output = subprocess.check_output(["obsidian-cli", "vaults"], text=True)
    vault_names = output.strip().split()
    return vault_names


class _VaultInfo(ty.NamedTuple):
    name: str
    path: Path


def _get_vault_info(vault_name: str) -> _VaultInfo:
    output = subprocess.check_output(["obsidian-cli", f"vault={vault_name}", "vault"], text=True)

    vault_info_dict = dict()
    for line in output.strip().splitlines():
        key, val = line.strip().split(maxsplit=1)
        vault_info_dict[key.strip()] = val.strip()

    return _VaultInfo(name=vault_info_dict["name"], path=Path(vault_info_dict["path"]))


class _FileInVault(ty.NamedTuple):
    vault_name: str
    file_relpath: str


class _VaultNotFoundException(FileNotFoundError):
    pass


def _xf_to_file_in_vault(p: Path) -> _FileInVault:
    p = p.resolve()

    for vault_info in map(_get_vault_info, _list_vault_names()):
        if p.is_relative_to(vault_info.path):
            return _FileInVault(
                vault_name=vault_info.name, file_relpath=str(p.relative_to(vault_info.path))
            )

    raise _VaultNotFoundException("Could not find vault root")


def obsidian_open(p: Path) -> bool:
    """wraps a utility on my PATH for opening a file in obsidian"""
    if shutil.which("obsidian-cli"):
        try:
            vault_name, file_relpath = _xf_to_file_in_vault(p)
            subprocess.check_call(
                ["obsidian-cli", f"vault={vault_name}", "open", f"path={file_relpath}", "newtab"]
            )
            return True
        except (subprocess.CalledProcessError, _VaultNotFoundException):
            pass
    return False
