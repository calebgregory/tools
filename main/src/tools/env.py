import shutil
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

# `.env.toml` does not exist until `require_env` copies the template, so the committed
# template and `.git` have to stand in for it when we look for the root.
_ROOT_MARKERS = (".env.toml", ".env.template.toml", ".git")


def _repo_root(start: Path) -> Path:
    """Nearest directory at or above `start` holding one of `_ROOT_MARKERS`.

    A filesystem walk rather than `git rev-parse`, so importing this module costs no
    subprocess; it is cheap enough for a shell prompt or a status line to pay per call.
    """
    for directory in (start, *start.parents):
        if any((directory / marker).exists() for marker in _ROOT_MARKERS):
            return directory
    raise EnvironmentError(f"found none of {_ROOT_MARKERS} at or above {start}")


_THIS_REPO_ROOT = _repo_root(Path(__file__).parent)
_ENV_TOML = _THIS_REPO_ROOT / ".env.toml"
_ENV_TEMPLATE = _THIS_REPO_ROOT / ".env.template.toml"

SECRET_DIR = _THIS_REPO_ROOT / ".secret"
"""Where a tool caches credentials it obtained for itself (OAuth tokens and the like), as
opposed to the ones a human types into `.env.toml`. Gitignored, per-machine."""


@dataclass
class ClaudeConfig:
    project_targets: dict[str, Path] = field(default_factory=dict)
    auto_memory_paths: dict[str, Path] = field(default_factory=dict)
    """Per-project override of the path used to derive the auto-memory key
    (`~/.claude/projects/<key>/memory/`). Defaults to the project target if
    unset. Required when Claude Code's auto-memory key was derived from an
    ancestor of the project target (e.g. when target=~/work/notes/personal-work
    but the auto-memory dir is keyed off ~/work/notes)."""


@dataclass
class GmailConfig:
    client_id: str = ""
    client_secret: str = ""
    """From an OAuth client of type "Desktop app" in the Google Cloud console. Google
    calls this a secret, but a desktop client cannot keep one — it is an identifier for
    the app, and the consent screen plus the cached token are what actually gate access."""


@dataclass
class ImmichConfig:
    server_url: str = ""
    api_key: str = ""


@dataclass
class MainVaultConfig:
    root: Path | None = None
    walked_file: Path | None = None


@dataclass
class WorkVaultCurrentProjectConfig:
    personal: Path | None = None  # src
    shared: Path | None = None  # target


@dataclass
class WorkVaultConfig:
    root: Path | None = None
    current_project: WorkVaultCurrentProjectConfig = field(default_factory=WorkVaultCurrentProjectConfig)


@dataclass
class VaultConfig:
    """as in, Obsidian vault"""

    main: MainVaultConfig = field(default_factory=MainVaultConfig)
    work: WorkVaultConfig = field(default_factory=WorkVaultConfig)


@dataclass
class TmuxConfig:
    dir_aliases: dict[str, str] = field(default_factory=dict)
    """Directories that tmux window titles name with an alias instead of the first few
    characters of the directory name, keyed by path. Paths may be written with `~`."""


@dataclass
class EnvTomlConfig:
    computer_name: str = ""
    claude: ClaudeConfig = field(default_factory=ClaudeConfig)
    gmail: GmailConfig = field(default_factory=GmailConfig)
    immich: ImmichConfig = field(default_factory=ImmichConfig)
    tmux: TmuxConfig = field(default_factory=TmuxConfig)
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
        },
        auto_memory_paths={
            project_name: path
            for project_name, path_str in claude_data.get("auto-memory-paths", {}).items()
            if (path := _expand_user(path_str))
        },
    )

    gmail_data = data.get("gmail", {})
    config.gmail = GmailConfig(
        client_id=gmail_data.get("client_id", ""),
        client_secret=gmail_data.get("client_secret", ""),
    )

    immich_data = data.get("immich", {})
    config.immich = ImmichConfig(
        server_url=immich_data.get("server_url", ""),
        api_key=immich_data.get("api_key", ""),
    )

    config.tmux = TmuxConfig(dir_aliases=data.get("tmux", {}).get("dir-aliases", {}))

    vault_data = data.get("vault", {})
    main_vault_data = vault_data.get("main", {})
    config.vault = VaultConfig(
        main=MainVaultConfig(
            root=_expand_user(main_vault_data.get("root")),
            walked_file=_expand_user(main_vault_data.get("walked-file")),
        )
    )

    if work_vault_data := vault_data.get("work", {}):
        config.vault.work = WorkVaultConfig(root=work_vault_data.get("root"))
        if current_project_data := work_vault_data.get("current-project", {}):
            personal, shared = (_expand_user(current_project_data.get(k)) for k in ("personal", "shared"))
            assert personal and shared
            config.vault.work.current_project = WorkVaultCurrentProjectConfig(personal, shared)

    return config


def require_env() -> EnvTomlConfig:
    env = load_env()
    if env is None:
        shutil.copy(_ENV_TEMPLATE, _ENV_TOML)
        raise EnvironmentError(".env.toml did not previously exist; fill it out now and re-run this script")
    return env
