#!/usr/bin/env -S uv run python
"""Claude Markdown Chat - A file-based chat interface for Claude AI

Edit your markdown file, save it, and Claude will respond directly in the file.
"""

import os
import re
import typing as ty
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from pathlib import Path

import litellm
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Separator to distinguish between user and assistant messages
USER_MARKER = "\n## user\n"
ASSISTANT_MARKER = "\n## assistant\n"
SEND_MARKER = "///go"

SYSTEM_MESSAGE = """\
You are a helpful assistant. Your responses are written directly into a markdown document that serves as both the chat history and the final artifact.

Formatting guidelines:
- Start sub-headings at ### (h3) since ## is reserved for conversation structure
- Use nested bullet points for hierarchical information, not nested headings
- Use fenced code blocks with language identifiers (```python, ```js, etc.)
- Prefer markdown tables for comparisons or structured data
- Use `backticks` for file names, functions, commands, and technical terms
- Avoid horizontal rules (---) as they conflict with document structure
- Be concise—this document is the artifact, avoid filler phrases

DO NOT SEND BACK PRIOR MESSAGES. Only send your response to the most recent user prompt.
"""


def _default_chat_path() -> Path:
    return Path(__file__).parent / f".chats/{datetime.now().strftime('%Y%m%d-%H%M%S')}-chat.md"


def _extract_file_references(base_dir: Path, text: str) -> list[Path]:
    """Extract file paths from markdown link syntax [](...) patterns"""
    pattern = r"\[\]\(([^)]+)\)"
    matches = re.findall(pattern, text)
    # Deduplicate while preserving order
    seen, unique_paths = set(), []
    for match in matches:
        path = Path(match)
        if not path.is_absolute():
            path = (base_dir / path).resolve()
        if path not in seen:
            seen.add(path)
            unique_paths.append(path)
    return unique_paths


def _load_file_content(file_path: Path) -> str:
    """Load file content and format it with headers, or return error message"""
    try:
        # Resolve path (relative to base_dir for relative paths, as-is for absolute)
        # Read file
        content = file_path.read_text()

        # Format with headers
        return f"[File: {file_path}]\n{content}\n[End of file]\n"
    except FileNotFoundError:
        return f"[File: {file_path}]\n**Error: File not found**\n[End of file]\n"
    except PermissionError:
        return f"[File: {file_path}]\n**Error: Permission denied**\n[End of file]\n"
    except UnicodeDecodeError:
        return f"[File: {file_path}]\n**Error: Cannot read binary file**\n[End of file]\n"
    except Exception as e:
        return f"[File: {file_path}]\n**Error: {str(e)}**\n[End of file]\n"


def _enrich_message_with_file_contents(base_dir: Path, message_content: str) -> str:
    """Extract file references from message and prepend their contents"""
    file_refs = _extract_file_references(base_dir, message_content)
    if not file_refs:
        return message_content

    file_contents = [_load_file_content(file_path) for file_path in file_refs]

    # Prepend file contents to message
    enriched = "".join(file_contents) + "\n" + message_content
    return enriched


def _parse_and_yield_messages(content: str, base_dir: Path) -> ty.Iterator[dict[str, str]]:
    """Parse the markdown file into a list of messages for the API"""
    enrich = partial(_enrich_message_with_file_contents, base_dir)

    # Split by markers
    parts = content.split(USER_MARKER)
    for part in parts[1:]:  # Skip first empty part
        part = part.strip()
        if not part:
            continue

        # Check if there's an assistant response
        if ASSISTANT_MARKER in part:
            user_part, assistant_part = part.split(ASSISTANT_MARKER, 1)
            user_text, assistant_text = user_part.strip(), assistant_part.strip()

            if user_text:
                yield {"role": "user", "content": enrich(user_text)}
            if assistant_text:
                yield {"role": "assistant", "content": assistant_text}
        else:
            # Just a user message
            yield {"role": "user", "content": enrich(part)}


@dataclass
class ModelConfig:
    name: str
    api_key: str


@dataclass
class State:
    file: Path
    model: ModelConfig
    processing: bool = False


def _new_content(existing_content: str, assistant_resp: str) -> str:
    return (
        "\n".join([existing_content.rstrip() + "\n", ASSISTANT_MARKER, assistant_resp, USER_MARKER]) + "\n"
    )


def _handle_file_change(state: State, event_src_path: str | bytes):
    if event_src_path != str(state.file):
        return

    if state.processing:
        print("- already processing; dropping event")
        return

    try:
        content = state.file.read_text()
    except Exception as e:
        print(f"- error reading file: {e}")
        return

    if SEND_MARKER not in content:
        print("- send marker not in content")
        return

    print("+ detected change with SEND marker. Processing...")
    state.processing = True

    try:
        content = content.replace(SEND_MARKER, "")

        messages = list(_parse_and_yield_messages(content, base_dir=state.file.parent))
        # any referenced files in the .md are relative to the chat_file

        if not messages:
            print("+ no messages found to send")
            return

        print(f"+ sending {len(messages)} message(s) to {state.model.name}...")

        response_text = ""

        stream = litellm.completion(
            model=state.model.name,
            api_key=state.model.api_key,
            messages=[{"role": "system", "content": SYSTEM_MESSAGE}, *messages],
            max_tokens=8096,
            thinking=litellm.AnthropicThinkingParam(type="enabled", budget_tokens=4000),
            stream=True,
        )

        for chunk in stream:
            assert isinstance(chunk, litellm.ModelResponseStream)
            delta = chunk.choices[0].delta
            if not delta:
                continue
            if reasoning := getattr(delta, "reasoning_content", None):
                print(reasoning, end="", flush=True)
            elif delta.content:
                response_text += delta.content

        print()

        # Write response back to file (content here is the original markdown content, not the streaming content)
        state.file.write_text(_new_content(content, response_text))
        print("+ response written to file!")

    except Exception as e:
        print(f"+ error processing request: {e}")
        # Write error to file
        state.file.write_text(_new_content(content, f"**Error:** {str(e)}"))

    finally:
        state.processing = False


class FileHandler(FileSystemEventHandler):
    def __init__(self, callback: ty.Callable[[str | bytes], None]):
        self.callback = callback

    def on_modified(self, event):
        """Called when the file is modified"""
        self.callback(event.src_path)


def _create_file_handler(file_path: Path, model: ModelConfig) -> FileHandler:
    """Create a file modification handler using a closure to maintain state"""
    state = State(file_path, model)
    return FileHandler(callback=partial(_handle_file_change, state))


def _model_config(model_name: str) -> ModelConfig:
    file_name = "anthropic-api" if model_name.startswith("claude") else "openai-api"
    api_key = (Path.home() / ".keys" / file_name).read_text().strip()
    return ModelConfig(name=model_name, api_key=api_key)


def main(chat_path: Path, model: ModelConfig):
    """Main entry point"""

    chat_path = chat_path.resolve()
    if not chat_path.exists():
        initial_content = f"#\n{USER_MARKER}\n"
        chat_path.write_text(initial_content)
        print(f"Created new chat file: {chat_path}")

    print(
        f"""
Watching {chat_path} for changes...
Model: {model.name}
Add '{SEND_MARKER}' to your file and save to send messages.
Press Ctrl+C to stop.
"""
    )

    # Set up file watcher
    event_handler = _create_file_handler(chat_path, model)
    observer = Observer()
    observer.schedule(event_handler, str(chat_path.parent), recursive=False)
    observer.start()

    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        print(" bye")
    finally:
        observer.stop()
        observer.join()


def cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="Chat with LLMs using markdown files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s chat.md --model claude-sonnet-4-20250514
  %(prog)s chat.md --model gpt-4
  %(prog)s chat.md --model o1

Environment variables:
  ANTHROPIC_API_KEY   - Required for Claude models
  OPENAI_API_KEY      - Required for OpenAI models
  MODEL               - Default model (can be overridden with --model)
        """,
    )
    parser.add_argument("chat_file", type=Path, nargs="?", help="Path to markdown chat file")
    parser.add_argument(
        "--model", "-m", type=str, help="Model to use (e.g., claude-sonnet-4-20250514, gpt-4, o1)"
    )
    args = parser.parse_args()

    # Determine model: CLI arg > env var > default
    model_name = args.model or os.getenv("MODEL") or "claude-opus-4-5-20251101"

    # LiteLLM automatically reads API keys from environment variables:
    # - ANTHROPIC_API_KEY for Claude models
    # - OPENAI_API_KEY for OpenAI models
    # - etc.

    main(
        chat_path=args.chat_file or _default_chat_path(),
        model=_model_config(model_name),
    )


if __name__ == "__main__":
    cli()
