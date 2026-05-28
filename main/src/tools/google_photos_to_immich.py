#!/usr/bin/env -S uv run python
"""Extract Google Takeout .tgz deliveries and upload them to a local immich
server via immich-go.

Workflow:

  --trial         extract just the first .tgz, then immich-go --dry-run
  --dry-run       extract everything, then immich-go --dry-run
  (no flags)      extract everything, then a real (committing) upload

Google Takeout splits one logical Takeout/ tree across multiple deliveries,
so every .tgz overlays into a single shared root — this is what immich-go
expects so album JSON sidecars resolve their photos. Trial extracts into
the same shared root so the work is reused (memoized) by later runs.

NOTE: @pure.magic() content-hashes Path inputs, so the first time we see a
50GB .tgz mops will SHA-256 the whole file before deciding cache hit/miss.
Hashes persist at ~/.thds/core/hash-cache, so subsequent runs are fast.
"""

import argparse
import logging
import subprocess
import typing as ty
from datetime import datetime, timezone
from pathlib import Path

from thds.core.project_root import find_project_root
from thds.mops import pure

from tools.env import require_env

logger = logging.getLogger(__name__)

_BASE = Path("/Volumes/seagate1tb/google-photo-migration")
_RAW_TGZ_DIR = _BASE / "raw/brittany"
_UNZIPPED_ROOT = _BASE / "unzipped/brittany"

_PROJECT_DIR = find_project_root(Path(__file__))
_MOPS_BLOB_ROOT = _PROJECT_DIR / ".mops"
_LOGS_DIR = _PROJECT_DIR / ".out/logs"


@pure.magic(pipeline_id="google-photos-to-immich", blob_root=_MOPS_BLOB_ROOT)
def _unzip(tgz: Path, dest_root: str) -> None:
    """Extract one .tgz directly into dest_root. Returns dest_root.

    Multiple Takeout deliveries share the same Takeout/ subtree on purpose,
    so calling this repeatedly with different tgzs and the same dest_root
    overlays them into a single merged tree.
    """
    dest_root_ = Path(dest_root)
    logger.warning(
        "extracting %s into %s (will overwrite same-named files already in dest)", tgz, dest_root_
    )
    dest_root_.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(["tar", "-xf", str(tgz), "-C", str(dest_root_)])


def _upload_with_immich_go(takeout_root: Path, *, log_file: Path, dry_run: bool) -> None:
    env = require_env()
    cmd = [
        "immich-go",
        "upload",
        "from-google-photos",
        "--server",
        env.immich.server_url,
        "--api-key",
        env.immich.api_key,
        *(["--dry-run"] if dry_run else []),
        "--concurrent-tasks=1",
        "--on-errors=4",
        f"--log-file={str(log_file)}",
        str(takeout_root),
    ]
    log_file.parent.mkdir(parents=True, exist_ok=True)
    # Mask the api key for logging.
    log_cmd = [("***" if part == env.immich.api_key else part) for part in cmd]
    logger.info("running: %s", " ".join(log_cmd))
    subprocess.check_call(cmd)


def main(*, src_tgz_dir: Path, unzip_dest_dir: Path, dry_run: bool, limit: ty.Optional[int]) -> None:
    now = datetime.now(tz=timezone.utc)
    tgzs = sorted(src_tgz_dir.glob("*.tgz"))
    if not tgzs:
        raise FileNotFoundError(f"no .tgz files found in {src_tgz_dir}")

    if limit is not None:
        tgzs = tgzs[:limit]
        logger.info("limit mode: %d archive(s)", len(tgzs))

    logger.info("extracting %d archive(s) into shared root %s", len(tgzs), unzip_dest_dir)
    for tgz in tgzs:
        _unzip(tgz, str(unzip_dest_dir))

    log_file = _LOGS_DIR / f"{now.isoformat(timespec='seconds')}.log"
    _upload_with_immich_go(unzip_dest_dir, log_file=log_file, dry_run=dry_run)


def cli() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="run immich-go in --dry-run mode (implied by --trial)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="extract only the first N archives (ignored if --trial)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    main(src_tgz_dir=_RAW_TGZ_DIR, unzip_dest_dir=_UNZIPPED_ROOT, dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    cli()
