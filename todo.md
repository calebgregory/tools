# todo

## share agent context between Claude and Codex

### Context and rationale

We keep instructions, coding and writing rules, skills, and project memory under
[lemons/](./lemons/README.md). Much of this describes how I work and applies to both
Claude and Codex. The current location makes shared guidance look specific to Claude.

The initial [Codex startup instructions](./lemons/codex/AGENTS.md) tell Codex to read the
Claude files. The [Codex bootstrap](./lemons/codex/bootstrap.py) installs those instructions
as `~/.codex/AGENTS.md`. This shares the text, but skill discovery depends on the
agent following instructions to scan the Claude skill directories. Native Codex
skill discovery needs skills installed in its discovery locations.

Move shared context into a common location and have both harnesses link to it.
Keep one canonical copy so a preference or workflow change reaches both tools
without maintaining parallel versions. Keep the bootstrap scripts and configuration
specific to each harness alongside their adapters.

### Proposed layout

```text
~/tools/
├── principles/
└── lemons/
    ├── _shared/
    │   ├── global/
    │   │   ├── instructions.md
    │   │   └── skills/
    │   ├── vault-main/
    │   └── work-org/
    ├── claude/
    │   ├── bootstrap.py
    │   └── settings.json
    └── codex/
        ├── bootstrap.py
        └── AGENTS.md
```

Move the bulk of the existing Claude documentation into `lemons/_shared/`, retaining
global and project scopes. Move the current global `rules/` contents into
`~/tools/principles/`: these are general coding, architecture, testing, and writing
principles, useful independently of either harness.

Split the current global `CLAUDE.md` by scope. Shared preferences, such as leaving
changes unstaged for review, belong in shared instructions. Claude-specific guidance,
such as its Slack connector workaround, belongs under `lemons/claude/`.

### Bootstrap and startup behavior

| Shared source | Claude | Codex |
|---|---|---|
| Global instructions | Load through `~/.claude/CLAUDE.md` | Read from `~/.codex/AGENTS.md` |
| `~/tools/principles/` | Symlink as `~/.claude/rules/` | Read every Markdown file at startup, respecting any path conditions |
| Global skills | Link individual folders into `~/.claude/skills/` | Link individual folders into `~/.agents/skills/` |
| Project skills | Link individual folders into `<project>/.claude/skills/` | Link individual folders into `<project>/.agents/skills/` |
| Project instructions and memory | Load the applicable shared project context | Load the same applicable shared project context |

Keep global and project configuration directories local to each harness. Install
individual authored skill folders into their real `.claude/skills` and
`.agents/skills` directories. Internal runtime directories such as `.trash` and
`synced` belong to the harness; keep them outside the shared sources. Install
project settings, instructions, agent definitions, and output styles as individual
links too, so linking a whole project `.claude` directory does not recreate the
same ownership problem.

Codex's native discovery supplies skill metadata at startup
and supports explicit selection and matching tasks to descriptions; see the
[skill discovery documentation](https://learn.chatgpt.com/docs/build-skills).

Keep the Codex startup adapter small: read shared global instructions, read
`principles/`, and load applicable project context. Let native skill discovery handle
the installed skills. Both harnesses should load skill bodies when needed.

### Migration work

1. Move shared instructions, reusable skills, and project memory into
   `lemons/_shared/`; move global rules into `principles/`.
2. Move the existing harness bootstrap scripts and configuration under
   `lemons/claude/` and `lemons/codex/`. Keep Claude settings, hooks, and agent
   definitions there until we explicitly adapt them for Codex. Review output styles
   for shared writing guidance versus harness-specific configuration.
3. Update both bootstraps to install links from the shared sources. Decide whether
   to move the current `[claude.project-targets]` and `[claude.auto-memory-paths]`
   configuration into a shared namespace, updating their readers together.
4. Adapt skill invocation metadata where needed. For example, preserve the explicit
   invocation requirement of `extract-principle`: Claude uses
   `disable-model-invocation: true`; Codex uses
   `policy.allow_implicit_invocation: false` in `agents/openai.yaml`.
5. Update path references, permissions, hook commands, ignore patterns, and bootstrap
   documentation. Account for existing installed symlinks so moving their targets
   does not leave the active configuration broken.
6. Verify first-time installation, repeat runs, existing-file protection, and link
   migration. In fresh sessions, verify that both harnesses load shared instructions
   and principles and discover global and project skills in the intended scope.

We ran both bootstraps on the work machine on 2026-10-26 and removed the temporary
compatibility symlinks and ignore entries. Fresh-session checks for both harnesses are
pending. Other machines need the same bootstrap run. See
[installation and migration](./lemons/README.md) for the bootstrap commands.
