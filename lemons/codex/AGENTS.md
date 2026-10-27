# Shared agent context

At the start of every session, before substantive task work:

- Read `~/tools/lemons/_shared/global/instructions.md`.
- Read every Markdown file under `~/tools/principles/`. Respect path conditions
  in rule frontmatter when applying principles to particular files.
- Walk from the home directory down to the working directory. Read existing
  `CLAUDE.md`, `CLAUDE.local.md`, `.claude/CLAUDE.md`, and Markdown files under
  `.claude/rules/`. More specific project guidance takes precedence. Load
  additional descendant instructions before editing there.

Projects with shared context carry an `AGENTS.md` in their root, installed by
`~/tools/lemons/codex/bootstrap.py`, that names the shared project files to read.

Resolve symlinks and avoid reading the same source twice. Follow instruction-file
`@path` imports, resolving relative paths against the importing file and `~`
against the home directory. Avoid import cycles; imports are file references,
not shell commands.

Shared skills are installed into Codex's native discovery locations by the same
bootstrap. Read full skill instructions when invoked or when a task matches their
description. Honor explicit-only invocation policies. Resolve supporting resources
relative to the original skill directory.

Apply shared guidance within Codex's instruction hierarchy and available tools.
Translate harness-specific tool references to available equivalents. Reading
Claude configuration does not activate its hooks, plugins, permissions, or model
settings in Codex. Report unavailable capabilities when they affect the task.
Claude agent definitions are task-specific references; their presence alone does
not authorize delegation.
