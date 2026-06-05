# mdformat-twospace

An [mdformat](https://github.com/hukkin/mdformat) plugin that puts **two spaces
after sentence-ending punctuation** (`.`, `:`, `?`, `!`) — the
[French-spacing](https://en.wikipedia.org/wiki/Sentence_spacing) convention — so
prose Markdown reads consistently regardless of how it was typed.

It runs as a text post-processor: it never changes the parsed document, only the
spacing in the rendered output.

## What it handles

- Sentence breaks within a single text node (`End.  Next.`).
- Breaks that **span inline nodes** — punctuation ending a text node before a
  following span (`Andrew:  __"..."__`), and a sentence ending inside a span and
  continuing after it (`**Done.**  Next.`).
- **False periods** left alone — abbreviations (`Mr.`, `e.g.`), single-letter
  initials (`J. R. R.`), and decimals (`3.14`).
- Never introduces trailing whitespace or hard breaks (end-of-line punctuation
  and `softbreak`/`hardbreak` siblings are skipped).

## Install

```sh
uv tool install -e /Users/calebgregory/tools/mdformat-twospace
```

mdformat discovers the plugin via its `mdformat.parser_extension` entry point;
enable it with `extensions=["twospace"]`.

## Usage

As a library:

```py
import mdformat
mdformat.text("People:  __We will.__\n", extensions=["twospace"])
```

CLI — formats a file in place:

```sh
2s path/to/file.md
```

## Use with pre-commit / prek

Add the package as an `additional_dependencies` of the mdformat hook:

```toml
[[repos]]
repo = "https://github.com/hukkin/mdformat"
rev = "1.0.0"
hooks = [
  { id = "mdformat", additional_dependencies = [
    "mdformat-gfm",
    "/Users/calebgregory/tools/mdformat-twospace",
  ] },
]
```

> [!IMPORTANT]
> **After editing this tool, run `prek clean` (or `pre-commit clean`) in every
> project that consumes it.**
>
> pre-commit/prek install `additional_dependencies` into an isolated, cached
> environment, keyed by the hook `rev` and the dependency strings — *not* by the
> contents of a local-path dependency. Because the path string and the package
> version don't change on every edit, the hook keeps running a stale snapshot of
> this tool until the cached environment is rebuilt. Bumping the version in
> `pyproject.toml` documents intent but does **not** force a rebuild on its own.

## Changes

See [CHANGES.md](CHANGES.md).
