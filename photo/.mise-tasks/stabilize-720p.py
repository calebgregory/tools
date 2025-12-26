#!/usr/bin/env -S uv run python
"""
ffmpeg + libvidstab takes place in two passes:
    1. analyze motion;
    2. apply transform, given analysis, to stabilize the video.

this script does that, along with resizing the video to 720p.  for our purposes,
we don't need more than that.

libvidstab is fairly featured, and depending on the particulars of the input
video, you may want to use different options.  maybe at some point i'll play
with that.  this is at least a decent starting point.
"""
from functools import partial

import argparse
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import timeit


def ffmpeg_analyze_motion(in_: Path, trf: Path, num_ffmpeg_threads: int) -> list[str]:
    return f"""
        ffmpeg -i {in_}
        -threads {num_ffmpeg_threads}
        -vf vidstabdetect=shakiness=5:accuracy=15:result={trf}
        -f null -
    """.strip().split()


def ffmpeg_stabilize_resize_and_encode(
    in_: Path, trf: Path, out: Path, num_ffmpeg_threads: int
) -> list[str]:
    stabilize_expr = f"vidstabtransform=input={trf}:smoothing=14:zoom=1:maxangle=2:maxshift=20"
    # 720p "smart scale": landscape -> height=720, portrait -> width=720 (aspect preserved)
    scale_expr = "scale='if(gte(iw,ih),-2,720):if(gte(iw,ih),720,-2)'"
    return f"""
        ffmpeg -i {in_}
        -threads {num_ffmpeg_threads}
        -vf {stabilize_expr},{scale_expr}
        -metadata:s:v:0 rotate=0
        -c:v libx264 -crf 20 -preset medium
        -c:a aac -b:a 160k
        {out}
    """.strip().split()


def transform_video(out_dir: Path, num_ffmpeg_threads: int, in_: Path) -> tuple[Path, float]:
    out = out_dir / f"{in_.stem}.720p-stabilized.mp4"

    if out.exists():
        print(f"already exists: {out}")
        return out, 0

    start = timeit.default_timer()
    with tempfile.NamedTemporaryFile(
        prefix=f"vidstab_{in_.name}.", suffix=".trf", delete=True, delete_on_close=False
    ) as tmp_trf:
        tmp_trf.close()  # close the file so ffmpeg can write to it
        trf = Path(tmp_trf.name)

        subprocess.run(ffmpeg_analyze_motion(in_, trf, num_ffmpeg_threads), check=True)

        subprocess.run(
            ffmpeg_stabilize_resize_and_encode(in_, trf, out, num_ffmpeg_threads),
            check=True,
        )

    end = timeit.default_timer()
    return out, end - start


def main(album_dir: Path, *, num_jobs: int, num_ffmpeg_threads: int) -> None:
    if shutil.which("ffmpeg") is None:
        raise EnvironmentError("Error: ffmpeg not found on PATH.")

    if not album_dir.is_dir():
        raise NotADirectoryError(album_dir)

    mov_files = sorted(album_dir.glob("*.MOV"))
    if not mov_files:
        raise FileNotFoundError(f"{album_dir} has no *.MOV files!")

    out_dir = album_dir / "720p-stabilized"
    out_dir.mkdir(parents=True, exist_ok=True)

    transform_video_ = partial(transform_video, out_dir, num_ffmpeg_threads)
    start = timeit.default_timer()
    with ThreadPoolExecutor(max_workers=max(1, num_jobs)) as ex:
        futures = {ex.submit(transform_video_, mov): mov for mov in mov_files}

        try:
            for i, fut in enumerate(as_completed(futures)):
                out, dur = fut.result()
                print(f"[{i+1}/{len(mov_files)}] done: {out} ({dur/60:0>5.2f} min)")
        except KeyboardInterrupt:
            print("Interrupted. Cancelling queued tasks...", file=sys.stderr)
            ex.shutdown(cancel_futures=True)
            return
        except Exception:
            ex.shutdown(cancel_futures=True)
            raise
    end = timeit.default_timer()
    print(f"done ({(end - start) / 60:0>5.2f} min)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("album_dir", type=Path, help="Directory containing .MOV files")
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--ffmpeg-threads", type=int, default=3)
    args = parser.parse_args()

    main(args.album_dir, num_jobs=args.jobs, num_ffmpeg_threads=args.ffmpeg_threads)
