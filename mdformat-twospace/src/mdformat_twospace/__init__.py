from __future__ import annotations

import typing as ty

if ty.TYPE_CHECKING:
    from markdown_it import MarkdownIt
    from mdformat.renderer.typing import Postprocess, Render

from .double_space import double_space


def update_mdit(mdit: MarkdownIt) -> None:
    """No parser changes — we only post-process already-rendered text."""


RENDERERS: ty.Mapping[str, Render] = {}
POSTPROCESSORS: ty.Mapping[str, Postprocess] = {"text": double_space}
