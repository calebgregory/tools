from __future__ import annotations

import re
import typing as ty
from pathlib import Path

if ty.TYPE_CHECKING:
    from mdformat.renderer import RenderContext, RenderTreeNode


def _load_abbreviations() -> ty.Iterable[str]:
    f = Path(__file__).parent / "known_abbreviations.txt"
    for line in f.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "#" in line:
            abbrev, _comment = line.split("#", 1)
        else:
            abbrev = line

        yield abbrev.strip()


_ABBREVIATIONS = frozenset(_load_abbreviations())

# Sentence-final punctuation + optional closing quote/paren.
_PUNCT = r"(?P<punct>[.:?!])(?P<close>[\"')\]]?)"
# A break fully contained in one text node: punct + one space + a non-space.
# Requiring a trailing non-space means we never touch end-of-line punctuation
# (so we never introduce trailing whitespace) and never match decimals like
# "3.14" (no space follows the dot).
_BREAK = re.compile(_PUNCT + r" (?P<next>\S)")
# Same punctuation sitting at the very end of a text node — a following inline
# sibling (not a space) supplies the start of the next sentence.
_TRAILING = re.compile(_PUNCT + r" $")
# A single leading space + non-space: a sentence that began in the previous
# inline sibling continues into this text node.
_LEADING = re.compile(r"^ \S")
_PRECEDING = re.compile(r"([A-Za-z][A-Za-z.]*)$")

# Inline siblings that render as a line break — never double-space against these
# (it would create trailing whitespace / a hard break).
_LINE_BREAKS = frozenset({"softbreak", "hardbreak"})
# Sibling spans whose trailing punctuation counts as a real prose sentence end.
# Excludes code_inline/html_inline: a '.' inside code is not a sentence boundary.
_PROSE_SPANS = frozenset({"strong", "em", "s", "link"})


def _is_false_period(text: str, dot_index: int) -> bool:
    """Whether the '.' at `dot_index` is a non-terminal period — an abbreviation
    (e.g. "Mr.", "e.g.") or a single-letter initial ("J. R. R.")."""
    before = _PRECEDING.search(text[:dot_index])
    if not before:
        return False
    token = before.group(1).rstrip(".").lower()
    return len(token) == 1 or token in _ABBREVIATIONS


def _last_text(node: RenderTreeNode) -> str | None:
    """Content of the last text-bearing descendant, for boundary inspection."""
    while getattr(node, "children", None):
        node = node.children[-1]
    return node.content if node.type == "text" else None


def _bump_trailing(text: str, node: RenderTreeNode | None) -> str:
    """Case A: punct ends this text node and a real inline span follows."""
    if node is None:
        return text
    nxt = node.next_sibling
    if nxt is None or nxt.type in _LINE_BREAKS:
        return text
    m = _TRAILING.search(text)
    if m is None:
        return text
    if m["punct"] == "." and _is_false_period(text, m.start("punct")):
        return text
    return text[: m.end("close")] + "  "


def _bump_leading(text: str, node: RenderTreeNode | None) -> str:
    """Case B: a sentence ended inside the previous span and continues here."""
    if node is None or not _LEADING.match(text):
        return text
    prev = node.previous_sibling
    if prev is None or prev.type not in _PROSE_SPANS:
        return text
    tail = _last_text(prev)
    if tail is None:
        return text
    stripped = tail.rstrip()
    if not stripped or stripped[-1] not in ".:?!":
        return text
    if stripped[-1] == "." and _is_false_period(stripped, len(stripped) - 1):
        return text
    return " " + text


def double_space(text: str, node: RenderTreeNode, context: RenderContext) -> str:
    def _sub(m: re.Match[str]) -> str:
        if m["punct"] == "." and _is_false_period(text, m.start("punct")):
            return m.group(0)
        return f"{m['punct']}{m['close']}  {m['next']}"

    text = _BREAK.sub(_sub, text)
    text = _bump_trailing(text, node)
    text = _bump_leading(text, node)
    return text
