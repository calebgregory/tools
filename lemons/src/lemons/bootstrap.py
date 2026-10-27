"""Install a harness's adapters and links to shared context.

A bootstrap plans the links for one harness, validates the whole plan against the disk, then
applies it. Validation failures leave the disk untouched.
"""

import typing as ty

from tools.env import LemonsConfig, require_env

from lemons import claude, codex, install, links

Harness = ty.Literal["claude", "codex"]

_PLANNER: ty.Final[ty.Mapping[Harness, ty.Callable[[LemonsConfig], links.Plan]]] = {
    "claude": claude.plan,
    "codex": codex.plan,
}


def bootstrap(harness: Harness) -> None:
    config = require_env().lemons

    plan = _PLANNER[harness](config)
    install.validate_plan(plan, config)

    install.apply(plan)
