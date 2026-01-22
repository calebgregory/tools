#!/bin/bash

alias transcribe="uv run python -m transcribe.__main__"

function transcribe-diarize() {
    # torchcodec requires FFmpeg 7 (not 8), use arm64 keg-only install
    DYLD_LIBRARY_PATH="/opt/homebrew/opt/ffmpeg@7/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}" \
        uv run python -m transcribe.diarize "$@"
}
