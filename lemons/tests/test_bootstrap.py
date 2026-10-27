import shutil
from pathlib import Path

import pytest
from lemons.bootstrap import Harness
from tools.env import EnvTomlConfig, LemonsConfig

from lemons import bootstrap, links


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _write_skill(directory: Path) -> None:
    _write(directory / "SKILL.md", f"---\nname: {directory.name}\ndescription: Test skill.\n---\n")


@pytest.fixture
def managed_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A home directory and a repository with one global skill and two mapped projects.

    `vault-main` maps to `~/vault` and has a skill and an output style. `work-org` maps to
    `~/work/.claude`, has a skill, an output style, shared memory, a Claude adapter file under
    `agents/`, a Codex adapter, and an auto-memory path override of `~/memory-root`.
    """
    repository = tmp_path / "repository"
    lemons = repository / "lemons"
    _write(repository / "principles/testing.md", "# Testing")
    _write_skill(lemons / "_shared/global/skills/extract-principle")
    _write_skill(lemons / "_shared/vault-main/skills/tidy")
    _write(lemons / "_shared/vault-main/output-styles/task-manager.md", "vault style")
    _write_skill(lemons / "_shared/work-org/skills/tidy")
    _write(lemons / "_shared/work-org/output-styles/work-task-manager.md", "work style")
    _write(lemons / "_shared/work-org/memory/MEMORY.md", "# Memory")
    _write(lemons / "claude/global/CLAUDE.md", "@shared instructions")
    _write(lemons / "claude/global/settings.json", "{}")
    _write(lemons / "claude/global/README.md", "not installed")
    (lemons / "claude/global/rules").symlink_to(Path("../../../principles"))
    _write(lemons / "claude/vault-main/settings.json", "{}")
    _write(lemons / "claude/work-org/CLAUDE.md", "@shared project instructions")
    _write(lemons / "claude/work-org/agents/apply-update.md", "agent")
    _write(lemons / "codex/AGENTS.md", "# Codex")
    _write(lemons / "codex/work-org/AGENTS.md", "# Codex work project")
    monkeypatch.setattr(links, "LEMONS_DIR", lemons)
    monkeypatch.setattr(links, "SHARED_DIR", lemons / "_shared")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.delenv("CODEX_HOME", raising=False)
    config = EnvTomlConfig(
        lemons=LemonsConfig(
            project_targets={
                "vault-main": tmp_path / "vault",
                "work-org": tmp_path / "work" / ".claude",
            },
            auto_memory_paths={"work-org": tmp_path / "memory-root"},
        )
    )
    monkeypatch.setattr(bootstrap, "require_env", lambda: config)
    (tmp_path / "vault").mkdir()
    (tmp_path / "work").mkdir()
    return tmp_path


def test_claude_installs_shared_context_and_memory(managed_home: Path) -> None:
    bootstrap.bootstrap("claude")
    bootstrap.bootstrap("claude")

    assert (managed_home / ".claude/rules").resolve() == links.LEMONS_DIR.parent / "principles"
    assert (managed_home / ".claude/skills/extract-principle").resolve() == (
        links.SHARED_DIR / "global/skills/extract-principle"
    )
    assert (managed_home / "vault/.claude/skills/tidy").resolve() == (
        links.SHARED_DIR / "vault-main/skills/tidy"
    )
    assert not (managed_home / "vault/.claude").is_symlink()
    assert not (managed_home / "vault/.claude/skills").is_symlink()
    assert not (managed_home / ".claude/skills").is_symlink()
    assert (managed_home / "vault/.claude/output-styles/task-manager.md").is_file()
    assert (managed_home / "work/.claude/memory/MEMORY.md").is_file()
    assert (managed_home / "work/.claude/output-styles/work-task-manager.md").is_file()
    memory_key = str(managed_home / "memory-root").replace("/", "-").replace(".", "-")
    assert (managed_home / ".claude/projects" / memory_key / "memory").resolve() == (
        links.SHARED_DIR / "work-org/memory"
    )


def test_codex_installs_skills_in_their_project_scopes(managed_home: Path) -> None:
    bootstrap.bootstrap("codex")
    bootstrap.bootstrap("codex")

    assert (managed_home / ".codex/AGENTS.md").resolve() == links.LEMONS_DIR / "codex/AGENTS.md"
    assert (managed_home / ".agents/skills/extract-principle").resolve() == (
        links.SHARED_DIR / "global/skills/extract-principle"
    )
    assert (managed_home / "vault/.agents/skills/tidy").resolve() == (
        links.SHARED_DIR / "vault-main/skills/tidy"
    )
    assert (managed_home / "work/.agents/skills/tidy").resolve() == (
        links.SHARED_DIR / "work-org/skills/tidy"
    )
    assert (managed_home / "work/AGENTS.md").resolve() == links.LEMONS_DIR / "codex/work-org/AGENTS.md"
    assert not (managed_home / "vault/AGENTS.md").exists()
    assert not (managed_home / ".agents/skills/tidy").exists()


def test_legacy_skills_directory_preserves_local_entries(managed_home: Path) -> None:
    legacy = managed_home / "legacy-skills"
    _write(legacy / "custom/SKILL.md", "local skill")
    target = managed_home / ".claude/skills"
    target.parent.mkdir()
    target.symlink_to(legacy)

    bootstrap.bootstrap("claude")

    assert target.is_dir() and not target.is_symlink()
    assert not (legacy / "custom").exists()
    assert not (target / "custom").is_symlink()
    assert (target / "custom/SKILL.md").read_text() == "local skill"
    assert (target / "extract-principle").resolve() == (
        links.SHARED_DIR / "global/skills/extract-principle"
    )


def test_project_conflict_prevents_partial_installation(managed_home: Path) -> None:
    conflict = managed_home / "work/.agents/skills/tidy"
    _write(conflict / "SKILL.md", "existing instructions")

    with pytest.raises(FileExistsError, match="move it aside"):
        bootstrap.bootstrap("codex")

    assert (conflict / "SKILL.md").read_text() == "existing instructions"
    assert not (managed_home / ".codex/AGENTS.md").exists()
    assert not (managed_home / "vault/.agents").exists()


def test_broken_legacy_directory_link_prevents_installation(managed_home: Path) -> None:
    (managed_home / "work/.claude").symlink_to(managed_home / "removed-checkout/claude/work-org")

    with pytest.raises(FileNotFoundError, match="Broken legacy directory link"):
        bootstrap.bootstrap("claude")

    assert (managed_home / "work/.claude").is_symlink()
    assert not (managed_home / ".claude").exists()


def test_migrates_link_even_when_compatibility_path_resolves(managed_home: Path) -> None:
    compatibility = managed_home / "old-codex"
    compatibility.symlink_to(links.LEMONS_DIR / "codex")
    target = managed_home / ".codex/AGENTS.md"
    target.parent.mkdir()
    target.symlink_to(compatibility / "AGENTS.md")

    bootstrap.bootstrap("codex")
    compatibility.unlink()

    assert target.readlink() == links.LEMONS_DIR / "codex/AGENTS.md"
    assert target.is_file()


@pytest.mark.parametrize("harness,variable", [("claude", "CLAUDE_CONFIG_DIR"), ("codex", "CODEX_HOME")])
def test_harness_home_override(
    managed_home: Path, monkeypatch: pytest.MonkeyPatch, harness: Harness, variable: str
) -> None:
    destination = managed_home / "custom-config"
    monkeypatch.setenv(variable, str(destination))

    bootstrap.bootstrap(harness)

    assert destination.is_dir()
    assert not (managed_home / f".{harness}").exists()


def test_claude_rerun_discovers_new_project_skills(managed_home: Path) -> None:
    bootstrap.bootstrap("claude")
    skill = links.SHARED_DIR / "work-org/skills/new-skill"
    _write_skill(skill)

    bootstrap.bootstrap("claude")

    assert (managed_home / "work/.claude/skills/new-skill").resolve() == skill


@pytest.mark.parametrize("harness", ["claude", "codex"])
def test_missing_project_root_prevents_installation(managed_home: Path, harness: Harness) -> None:
    (managed_home / "vault").rmdir()

    with pytest.raises(FileNotFoundError, match="Project root does not exist"):
        bootstrap.bootstrap(harness)

    assert not (managed_home / "vault").exists()
    assert not (managed_home / ".claude").exists()
    assert not (managed_home / ".codex").exists()
    assert not (managed_home / ".agents").exists()


def test_memory_key_change_names_both_keys(managed_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config = bootstrap.require_env().lemons
    config.auto_memory_paths.clear()
    target = config.project_targets["work-org"]
    old_key = str(target.resolve()).replace("/", "-").replace(".", "-")
    new_key = str(target.parent.resolve()).replace("/", "-").replace(".", "-")
    old_link = managed_home / ".claude/projects" / old_key / "memory"
    old_link.parent.mkdir(parents=True)
    old_link.symlink_to(links.SHARED_DIR / "work-org/memory")

    bootstrap.bootstrap("claude")

    assert f"Auto-memory key changes from {old_key} to {new_key}" in capsys.readouterr().out
    assert old_link.is_symlink()
    assert (managed_home / ".claude/projects" / new_key / "memory").is_dir()


def test_project_directory_migration_preserves_runtime_artifacts(managed_home: Path) -> None:
    legacy = links.LEMONS_DIR / "claude/work-org"
    _write(legacy / "skills/.trash/old-skill.md", "preserve me")
    (managed_home / "work/.claude").symlink_to(legacy)

    bootstrap.bootstrap("claude")
    bootstrap.bootstrap("claude")

    target = managed_home / "work/.claude"
    assert not target.is_symlink()
    assert not (target / "skills").is_symlink()
    assert not (target / "skills/.trash").is_symlink()
    assert (target / "skills/.trash/old-skill.md").read_text() == "preserve me"
    assert not (legacy / "skills/.trash").exists()
    assert (target / "skills/tidy").resolve() == links.SHARED_DIR / "work-org/skills/tidy"


def test_global_migration_moves_artifacts_out_of_shared_sources(managed_home: Path) -> None:
    artifact = links.SHARED_DIR / "global/skills/synced"
    _write(artifact / "state.json", "local runtime state")
    legacy = links.LEMONS_DIR / "claude/global/skills"
    legacy.mkdir()
    (legacy / "synced").symlink_to(artifact)
    destination = managed_home / ".claude/skills"
    destination.parent.mkdir()
    destination.symlink_to(legacy)

    bootstrap.bootstrap("claude")
    bootstrap.bootstrap("claude")

    assert not artifact.exists()
    assert not (destination / "synced").is_symlink()
    assert (destination / "synced/state.json").read_text() == "local runtime state"


def test_runtime_skill_artifacts_stay_outside_repository(managed_home: Path) -> None:
    bootstrap.bootstrap("claude")
    bootstrap.bootstrap("codex")
    targets = [
        managed_home / ".claude/skills",
        managed_home / ".agents/skills",
        managed_home / "vault/.claude/skills",
        managed_home / "vault/.agents/skills",
        managed_home / "work/.claude/skills",
        managed_home / "work/.agents/skills",
    ]
    for target in targets:
        _write(target / ".trash/state", "local")

    bootstrap.bootstrap("claude")
    bootstrap.bootstrap("codex")

    assert not list(links.LEMONS_DIR.rglob(".trash"))
    assert all((target / ".trash/state").read_text() == "local" for target in targets)


def test_claude_links_every_project_adapter_file(managed_home: Path) -> None:
    command = links.LEMONS_DIR / "claude/work-org/commands/review.md"
    _write(command, "review")
    _write(links.LEMONS_DIR / "claude/work-org/README.md", "not installed")

    bootstrap.bootstrap("claude")

    installed = managed_home / "work/.claude"
    assert (installed / "commands/review.md").readlink() == command
    assert not (installed / "commands").is_symlink()
    assert not (installed / "README.md").exists()


def test_unmanaged_repository_entry_prevents_migration(managed_home: Path) -> None:
    legacy = links.LEMONS_DIR / "claude/global/skills"
    unlinked = legacy / "draft-skill/notes.md"
    _write(unlinked, "not linked by the bootstrap")
    installed = managed_home / ".claude/skills"
    installed.parent.mkdir()
    installed.symlink_to(legacy)

    with pytest.raises(FileExistsError, match="no link manages it"):
        bootstrap.bootstrap("claude")

    assert installed.is_symlink()
    assert unlinked.read_text() == "not linked by the bootstrap"


def test_removed_sources_leave_no_stale_links(managed_home: Path) -> None:
    bootstrap.bootstrap("claude")
    bootstrap.bootstrap("codex")
    foreign = managed_home / "foreign-skill"
    foreign.mkdir()
    (managed_home / ".claude/skills/foreign").symlink_to(foreign)
    shutil.rmtree(links.SHARED_DIR / "work-org/skills/tidy")
    (links.LEMONS_DIR / "claude/work-org/agents/apply-update.md").unlink()

    bootstrap.bootstrap("claude")
    bootstrap.bootstrap("codex")

    assert not (managed_home / "work/.claude/skills/tidy").is_symlink()
    assert not (managed_home / "work/.agents/skills/tidy").is_symlink()
    assert not (managed_home / "work/.claude/agents/apply-update.md").is_symlink()
    assert (managed_home / "vault/.claude/skills/tidy").is_symlink()
    assert (managed_home / ".claude/skills/foreign").readlink() == foreign
