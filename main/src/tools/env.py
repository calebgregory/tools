import shutil
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from tools import git

_ENV_TOML = git.repo_root() / ".env.toml"
_ENV_TEMPLATE = git.repo_root() / ".env.template.toml"


@dataclass
class ClaudeConfig:
    project_targets: dict[str, Path] = field(default_factory=dict)


@dataclass
class VaultConfig:
    """as in, Obsidian vault"""

    walked_file: Path | None = None


@dataclass
class EnvTomlConfig:
    computer_name: str = ""
    claude: ClaudeConfig = field(default_factory=ClaudeConfig)
    vault: VaultConfig = field(default_factory=VaultConfig)


def load_env() -> EnvTomlConfig | None:
    if not _ENV_TOML.exists():
        return None
    with _ENV_TOML.open("rb") as f:
        data = tomllib.load(f)

    claude_data = data.get("claude", {})
    claude_config = ClaudeConfig(
        project_targets={
            project_name: Path(target_str).expanduser()
            for project_name, target_str in claude_data.get("project-targets", {}).items()
            if target_str
        }
    )

    vault_data = data.get("vault", {})
    vault_config = VaultConfig(
        walked_file=Path(walked_file).expanduser()
        if (walked_file := vault_data.get("walked-file"))
        else None
    )

    return EnvTomlConfig(
        computer_name=data.get("computer_name", ""),
        claude=claude_config,
        vault=vault_config,
    )


def require_env() -> EnvTomlConfig:
    env = load_env()
    if env is None:
        shutil.copy(_ENV_TEMPLATE, _ENV_TOML)
        raise EnvironmentError(".env.toml did not previously exist; fill it out now and re-run this script")
    return env
