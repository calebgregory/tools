"""Refine transcript using LLM to assign unknown speakers and add punctuation."""

from pathlib import Path

from litellm import completion

SYSTEM_PROMPT = """\
You are a transcript editor. You will receive a raw transcript with speaker labels.

Your tasks:
1. **Assign UNKNOWN speakers**: When you see "UNKNOWN:", analyze the context (what was said before/after, conversation flow) to determine which speaker most likely said it. Replace "UNKNOWN" with the appropriate speaker label (e.g., SPEAKER_00, SPEAKER_01, etc.).

2. **Add punctuation**: The transcript has no punctuation. Add appropriate punctuation (periods, commas, question marks, exclamation points) to make it readable while preserving the exact words.

3. **Mark interruptions**: Add "--" at the end of a speaker's text anytime they are interrupted by another speaker.

4. **Preserve the format**: Keep the same format with speaker labels followed by colon and their text. Keep paragraph breaks between speaker changes.

5. **Do not change words**: Only add punctuation, mark interruptions, and reassign UNKNOWN speakers. Do not add, remove, or modify any words.

Output only the refined transcript, nothing else."""


def refine_transcript(transcript_path: Path, workdir: Path, model: str = "gpt-4o") -> Path:
    """
    Use an LLM to refine the transcript by:
    - Assigning UNKNOWN speakers based on context
    - Adding punctuation for readability
    - Marking interruptions with "--"
    """
    raw_transcript = transcript_path.read_text(encoding="utf-8")

    response = completion(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_transcript},
        ],
        temperature=0.3,
    )

    refined_text = response.choices[0].message.content

    out_path = workdir / "transcript.refined.txt"
    out_path.write_text(refined_text, encoding="utf-8")
    print(f"Wrote: {out_path}")

    return out_path
