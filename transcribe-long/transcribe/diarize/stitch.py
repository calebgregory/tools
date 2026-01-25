"""Stitch diarized chunks using LLM for punctuation and formatting.

DEAD CODE!!!"""

from litellm import completion
from thds.core.source import Source

from transcribe.config import TranscribeConfig
from transcribe.diarize.types import DiarizedChunkTranscript
from transcribe.workdir import workdir

STITCH_PROMPT = """You are formatting a transcript from multiple audio chunks. Each chunk has
speaker labels in the format CHUNK_N_X (e.g., CHUNK_0_A, CHUNK_0_B, CHUNK_1_A).

Your tasks:

1. **Add punctuation**: Add appropriate punctuation for readability.

2. **Mark chunk boundaries**: At the END of each chunk's last segment, add "..."
   if the text appears to end mid-sentence or mid-thought. At the START of
   each chunk's first segment, add "..." if it appears to continue from the
   previous chunk.

3. **Preserve speaker labels**: Keep all CHUNK_N_X labels exactly as provided.
   Do NOT attempt to unify or rename speakers.

4. **Preserve all words**: Do not remove or add words (except "..." markers and punctuation).

5. **Add paragraph breaks**: Add blank lines between speaker turns for readability.

Output format:
CHUNK_0_A: Their complete text here.

CHUNK_0_B: Their response here...

CHUNK_1_A: ...continuing from previous chunk.

CHUNK_1_B: New speaker in this chunk.

Here are the chunks to format:

{chunks_text}

Output the formatted transcript:"""


def _format_chunk_for_llm(transcript: DiarizedChunkTranscript) -> str:
    """Format a chunk's segments for the LLM prompt."""
    lines = [f"--- CHUNK {transcript.index} ---"]
    for seg in transcript.segments:
        lines.append(f"{seg.speaker}: {seg.text}")
    return "\n".join(lines)


def stitch_diarized_chunks(transcripts: list[DiarizedChunkTranscript], config: TranscribeConfig) -> Source:
    """
    Stitch diarized chunks using LLM for punctuation and formatting.

    The LLM adds:
    - Punctuation for readability
    - "..." markers at chunk boundaries where sentences appear split
    - Paragraph breaks between speaker turns

    Speaker labels (CHUNK_N_X) are preserved as-is.
    """
    transcripts = sorted(transcripts, key=lambda t: t.index)

    # Format all chunks for the LLM
    chunks_text = "\n\n".join(_format_chunk_for_llm(t) for t in transcripts)

    # Call LLM to format the transcript
    print(f"Stitching transcript with {config.reformat_model}...")
    response = completion(
        model=config.reformat_model,
        messages=[{"role": "user", "content": STITCH_PROMPT.format(chunks_text=chunks_text)}],
        temperature=0.1,  # Low temperature for consistent formatting
    )

    formatted_text = response.choices[0].message.content or ""

    # Write output
    out_txt = workdir() / "transcript.txt"
    out_txt.write_text(formatted_text.strip() + "\n", encoding="utf-8")
    print(f"Wrote: {out_txt}")

    return Source.from_file(out_txt)
