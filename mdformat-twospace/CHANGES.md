# Changes

## 0.2.1

- Adds `est.` to known-abbreviations

## 0.2.0

- Move the core into `double_space.py` and handle sentence boundaries that span
  inline nodes: punctuation ending a text node before a following span (Case A),
  and a sentence ending inside a preceding span and continuing after it (Case B).
- Skip false periods — abbreviations (`Mr.`, `e.g.`), single-letter initials
  (`J. R. R.`), and decimals (`3.14`).
- Never double-space against `softbreak`/`hardbreak` siblings or end-of-line
  punctuation (avoids introducing trailing whitespace / hard breaks).
- Add a `2s` CLI entry point.

## 0.1.0

- Initial release: two spaces after sentence-ending punctuation within a single
  text node.
