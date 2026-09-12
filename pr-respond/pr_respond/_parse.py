import re
from datetime import datetime
from pathlib import Path

from ._types import NewComment, ParsedReview, PRMetadata, Reply


def _parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not match:
        raise ValueError("Missing YAML frontmatter")

    frontmatter_text = match.group(1)
    body = match.group(2)

    frontmatter = {}
    for line in frontmatter_text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip()

    return frontmatter, body


def _extract_review_body(body: str) -> str | None:
    match = re.search(
        r"## Review Body\n\n(.*?)(?=\n---|\n## )", body, re.DOTALL
    )
    if not match:
        return None

    text = match.group(1).strip()
    if text.startswith("<!--") and text.endswith("-->"):
        return None
    if not text or text.isspace():
        return None

    return text


def _extract_replies(body: str) -> list[Reply]:
    pattern = r"<!-- REPLY:(\d+) -->\n(.*?)\n<!-- /REPLY -->"
    replies = []

    for match in re.finditer(pattern, body, re.DOTALL):
        comment_id = int(match.group(1))
        reply_body = match.group(2).strip()

        if reply_body:
            replies.append(Reply(comment_id=comment_id, body=reply_body))

    return replies


def _extract_new_comments(body: str) -> list[NewComment]:
    pattern = r"<!-- NEW:([^:]+):(\d+)(?:-(\d+))? -->\n(.*?)\n<!-- /NEW -->"
    comments = []

    for match in re.finditer(pattern, body, re.DOTALL):
        path = match.group(1)
        first_num = int(match.group(2))
        second_num = int(match.group(3)) if match.group(3) else None
        comment_body = match.group(4).strip()

        if comment_body and path != "example/path.ts":
            # For ranges like 40-45: first_num=40 (start), second_num=45 (end/line)
            # For single line like 42: first_num=42, second_num=None
            start_line = first_num if second_num else None
            line = second_num if second_num else first_num
            comments.append(
                NewComment(path=path, line=line, start_line=start_line, body=comment_body)
            )

    return comments


def _require_field(frontmatter: dict[str, str], field: str) -> str:
    if field not in frontmatter:
        raise ValueError(f"Missing required field '{field}' in frontmatter")
    return frontmatter[field]


def parse(file_path: Path) -> ParsedReview:
    content = file_path.read_text()
    frontmatter, body = _parse_frontmatter(content)

    metadata = PRMetadata(
        pr_number=int(_require_field(frontmatter, "pr")),
        repo=_require_field(frontmatter, "repo"),
        title=frontmatter.get("title", ""),
        head_sha=_require_field(frontmatter, "head_sha"),
        fetched_at=datetime.fromisoformat(_require_field(frontmatter, "fetched_at")),
    )

    review_body = _extract_review_body(body)
    replies = _extract_replies(body)
    new_comments = _extract_new_comments(body)

    return ParsedReview(
        metadata=metadata,
        review_body=review_body,
        replies=replies,
        new_comments=new_comments,
    )
