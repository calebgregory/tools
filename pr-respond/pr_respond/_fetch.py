import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from github.PullRequest import PullRequest

from ._github import get_client
from ._types import CommentInfo, CommentThread, PRMetadata


def _parse_pr_ref(pr_ref: str) -> tuple[str, int]:
    """Parse PR reference like 'owner/repo#123' or full URL."""
    url_match = re.match(r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)", pr_ref)
    if url_match:
        return url_match.group(1), int(url_match.group(2))

    short_match = re.match(r"([^/]+/[^/]+)#(\d+)", pr_ref)
    if short_match:
        return short_match.group(1), int(short_match.group(2))

    raise ValueError(
        f"Invalid PR reference: {pr_ref}. Use 'owner/repo#123' or full GitHub URL."
    )


def _fetch_comments(pr: PullRequest) -> list[CommentThread]:
    comments_by_id: dict[int, CommentInfo] = {}
    replies_by_parent: dict[int, list[CommentInfo]] = defaultdict(list)

    for c in pr.get_review_comments():
        info = CommentInfo(
            id=c.id,
            path=c.path,
            line=c.line or c.original_line or 0,
            start_line=c.start_line,
            side=c.side or "RIGHT",
            body=c.body,
            user=c.user.login if c.user else "unknown",
            created_at=c.created_at,
            in_reply_to_id=c.in_reply_to_id,
        )
        comments_by_id[c.id] = info
        if c.in_reply_to_id:
            replies_by_parent[c.in_reply_to_id].append(info)

    threads = []
    for comment in comments_by_id.values():
        if comment.in_reply_to_id is None:
            replies = sorted(replies_by_parent[comment.id], key=lambda r: r.created_at)
            threads.append(CommentThread(root=comment, replies=replies))

    return sorted(threads, key=lambda t: (t.root.path, t.root.line))


def _format_markdown(metadata: PRMetadata, threads: list[CommentThread]) -> str:
    lines = [
        "---",
        f"pr: {metadata.pr_number}",
        f"repo: {metadata.repo}",
        f"title: {metadata.title}",
        f"head_sha: {metadata.head_sha}",
        f"fetched_at: {metadata.fetched_at.isoformat()}",
        "---",
        "",
        f"# PR #{metadata.pr_number}: {metadata.title}",
        "",
        "## Review Body",
        "",
        "<!-- Write your overall review comment here. Delete this section if not needed. -->",
        "",
        "---",
        "",
    ]

    threads_by_path: dict[str, list[CommentThread]] = defaultdict(list)
    for thread in threads:
        threads_by_path[thread.root.path].append(thread)

    for path in sorted(threads_by_path.keys()):
        lines.append(f"## {path}")
        lines.append("")

        for thread in threads_by_path[path]:
            root = thread.root
            line_str = (
                f"Line {root.start_line}-{root.line}"
                if root.start_line
                else f"Line {root.line}"
            )
            lines.append(f"### {line_str} (comment:{root.id})")
            lines.append("")
            lines.append(f"**@{root.user}** ({root.created_at.strftime('%Y-%m-%d')}):")
            for body_line in root.body.split("\n"):
                lines.append(f"> {body_line}")
            lines.append("")

            for reply in thread.replies:
                lines.append(
                    f"**@{reply.user}** ({reply.created_at.strftime('%Y-%m-%d')}) [reply]:"
                )
                for body_line in reply.body.split("\n"):
                    lines.append(f"> {body_line}")
                lines.append("")

            lines.append(f"<!-- REPLY:{root.id} -->")
            lines.append("")
            lines.append("<!-- /REPLY -->")
            lines.append("")
            lines.append("---")
            lines.append("")

    lines.extend(
        [
            "## NEW COMMENTS",
            "",
            "<!--",
            "Add new inline comments below. Format:",
            "  Single line:  < !-- NEW:path/to/file.ts:42 -- >",
            "  Multi-line:   < !-- NEW:path/to/file.ts:40-45 -- >",
            "  (remove spaces from the markers above)",
            "-->",
            "",
        ]
    )

    return "\n".join(lines)


def fetch(pr_ref: str, output: Path | None = None) -> Path:
    repo_name, pr_number = _parse_pr_ref(pr_ref)
    gh = get_client()
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    metadata = PRMetadata(
        pr_number=pr_number,
        repo=repo_name,
        title=pr.title,
        head_sha=pr.head.sha,
        fetched_at=datetime.now(timezone.utc),
    )

    threads = _fetch_comments(pr)
    markdown = _format_markdown(metadata, threads)

    output_path = output or Path(f"pr-{pr_number}-comments.md")
    output_path.write_text(markdown)

    return output_path
