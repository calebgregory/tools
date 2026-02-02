---
name: projects
description: Show which projects have open tasks and how many. Use when the user wants a project-level overview.
---

# Projects Overview

Scan the vault for all `todo.md` files and summarize open tasks by project.

## Steps

1. Find all `todo.md` files under the vault root (skip `.obsidian/`, `.git/`, `node_modules/`, `.venv/`, `_archive/`)
2. Read each file
3. Count open tasks (`- [ ]`) per file
4. Group by project

## Output format

```
## Projects

| Project | Open | File |
|---------|------|------|
| (personal) | N | todo/todo.md + todo/contact.md |
| andrew-and-kayla-wedding | N | planning + meetings + ideation |
| dance (AJA) | N | projects/dance/todo.md |
| woodworking/yoga_wall | N | projects/woodworking/yoga_wall/todo.md |
| home | N | home/todo.md |
| **Total** | **N** | |
```

## Rules

- Only show projects that have at least 1 open task
- For the wedding project, roll up all 3 todo files into one row but note the breakdown
- Sort by open task count descending
- If a new `todo.md` is discovered that isn't in the known list, include it and note it's new
