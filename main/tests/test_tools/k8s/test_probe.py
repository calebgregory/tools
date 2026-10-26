import pytest
from tools.k8s import _probe

_PS_OUTPUT = """\
      1     624 python -m thds.core.exit_after -s 36000
     37     611 bash /root/orchestrator-init.sh
    248     264 uv run ./scripts/katamari/run.py 202611 20261019.1 1p --env prod --register
    251     264 /app/intake/.venv/bin/python3 ./scripts/katamari/run.py 202611 20261019.1 1p --env prod --register
    299     252 /app/intake/.venv/bin/python3 -c from thds.mops.k8s.cost.daemon import main; main() {"owner_pid":251}
    900      10 /app/intake/.venv/bin/python3 ./scripts/katamari/run.py 202611 20261019.2 1p
"""


@pytest.mark.parametrize(
    ("pattern", "expected"),
    [
        (_probe.DEFAULT_POD_PROCESS_PATTERN, 251),  # the python process, not `uv run`; oldest wins
        (r"uv run", 248),
        (r"exit_after", 1),
        (r"nothing-like-this", None),
    ],
)
def test_oldest_matching_pid(pattern: str, expected: int | None) -> None:
    assert _probe.oldest_matching_pid(_PS_OUTPUT, pattern) == expected


def test_oldest_matching_pid_skips_short_lines() -> None:
    assert _probe.oldest_matching_pid("12 5\n\n", r".") is None
