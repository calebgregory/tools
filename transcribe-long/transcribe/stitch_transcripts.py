#!/usr/bin/env -S uv run python
from litellm import completion
from thds.core.source import Source

from transcribe.config import TranscribeConfig
from transcribe.transcribe_chunks import ChunkTranscript
from transcribe.workdir import workdir

REFORMAT_SYSTEM_PROMPT = """\
You are a transcript editor. The user will provide a transcript that has been \
stitched together from multiple audio fragments. Because of this fragmentation, \
some sentences may have incorrect capitalization or punctuation at the boundaries \
where fragments were joined.

Your task:
1. Correct any capitalization errors (e.g., lowercase letter at the start of a sentence)
2. Correct any punctuation errors (e.g., missing periods, incorrect comma placement at boundaries)
3. Add paragraph breaks where natural topic or speaker changes occur

CRITICAL RULES:
- You may ONLY change whitespace (spaces, newlines) and capitalization/punctuation
- Do NOT change any words, add words, remove words, or rephrase anything
- Do NOT add any commentary, headers, or formatting beyond paragraph breaks
- Return ONLY the corrected transcript text, nothing else
"""


def _reformat_transcript(text: str, model: str) -> str:
    """
    Send the stitched transcript to an LLM to fix capitalization/punctuation
    and add paragraph breaks.
    """
    response = completion(
        model=model,
        messages=[
            {"role": "system", "content": REFORMAT_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    content = response.choices[0].message.content
    return content.strip() if content else text


def stitch_transcripts(chunk_transcripts: list[ChunkTranscript], config: TranscribeConfig) -> Source:
    chunk_transcripts = sorted(chunk_transcripts, key=lambda t: t.index)

    txt_parts = [txt for t in chunk_transcripts if (txt := t.text.strip())]

    if not txt_parts:
        raise ValueError("No text found in transcripts.")

    out_raw = workdir() / "transcript.raw.txt"
    out_txt = workdir() / "transcript.txt"

    raw_text = "\n\n".join(txt_parts)
    out_raw.write_text(raw_text + "\n", encoding="utf-8")
    print(f"Wrote: {out_raw}")

    print(f"Reformatting with {config.reformat_model}...")
    reformatted = _reformat_transcript(raw_text, config.reformat_model)
    out_txt.write_text(reformatted + "\n", encoding="utf-8")
    print(f"Wrote: {out_txt}")

    return Source.from_file(out_txt)
