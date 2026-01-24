#!/bin/bash

this_dir=~/tools/transcribe-long

alias transcribe="uv --project ${this_dir} run python -m transcribe"
alias transcribe-diarize="uv --project ${thid_dir} run python -m transcribe.diarize"
alias transcribe-label="uv --project ${thid_dir} run python -m transcribe.diarize.label"
