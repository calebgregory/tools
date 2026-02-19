import shutil
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from tools import git

_THIS_REPO_ROOT = git.repo_root(Path(__file__))
print(_THIS_REPO_ROOT)
_ENV_TOML = _THIS_REPO_ROOT / ".env.toml"
_ENV_TEMPLATE = _THIS_REPO_ROOT / ".env.template.toml"


@dataclass
class ClaudeConfig:
    project_targets: dict[str, Path] = field(default_factory=dict)


@dataclass
class MainVaultConfig:
    root: Path | None = None
    walked_file: Path | None = None


@dataclass
class VaultConfig:
    """as in, Obsidian vault"""

    main: MainVaultConfig = field(default_factory=MainVaultConfig)


@dataclass
class EnvTomlConfig:
    computer_name: str = ""
    claude: ClaudeConfig = field(default_factory=ClaudeConfig)
    vault: VaultConfig = field(default_factory=VaultConfig)


def _expand_user(s: str | None) -> Path | None:
    return Path(s).expanduser() if s else None


def load_env() -> EnvTomlConfig | None:
    if not _ENV_TOML.exists():
        return None
    with _ENV_TOML.open("rb") as f:
        data = tomllib.load(f)

    config = EnvTomlConfig()
    config.computer_name = data.get("computer_name", "")

    claude_data = data.get("claude", {})
    config.claude = ClaudeConfig(
        project_targets={
            project_name: target
            for project_name, target_str in claude_data.get("project-targets", {}).items()
            if (target := _expand_user(target_str))
        }
    )

    main_vault_data = data.get("vault", {}).get("main", {})
    config.vault = VaultConfig(
        main=MainVaultConfig(
            root=_expand_user(main_vault_data.get("root")),
            walked_file=_expand_user(main_vault_data.get("walked-file")),
        )
    )

    return config


def require_env() -> EnvTomlConfig:
    env = load_env()
    if env is None:
        shutil.copy(_ENV_TEMPLATE, _ENV_TOML)
        raise EnvironmentError(".env.toml did not previously exist; fill it out now and re-run this script")
    return env
