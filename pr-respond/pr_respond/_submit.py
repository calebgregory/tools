from github.GithubException import GithubException
from github.PullRequest import ReviewComment

from ._github import get_client
from ._types import ParsedReview


def diff(review: ParsedReview, event: str = "COMMENT") -> str:
    lines = ["Would submit:", ""]

    if review.replies:
        lines.append(f"REPLIES ({len(review.replies)}):")
        for reply in review.replies:
            preview = reply.body[:60] + "..." if len(reply.body) > 60 else reply.body
            lines.append(f"  - Reply to comment #{reply.comment_id}")
            lines.append(f'    "{preview}"')
            lines.append("")

    if review.new_comments or review.review_body:
        lines.append(f"NEW REVIEW ({event}):")
        if review.review_body:
            preview = (
                review.review_body[:60] + "..."
                if len(review.review_body) > 60
                else review.review_body
            )
            lines.append(f'  Body: "{preview}"')
            lines.append("")

        if review.new_comments:
            lines.append(f"  Inline comments ({len(review.new_comments)}):")
            for comment in review.new_comments:
                line_str = (
                    f"{comment.start_line}-{comment.line}"
                    if comment.start_line
                    else str(comment.line)
                )
                preview = (
                    comment.body[:50] + "..."
                    if len(comment.body) > 50
                    else comment.body
                )
                lines.append(f"    - {comment.path}:{line_str}")
                lines.append(f'      "{preview}"')
                lines.append("")

    if not review.replies and not review.new_comments and not review.review_body:
        lines.append("Nothing to submit. Add replies or new comments to the markdown.")

    return "\n".join(lines)


def submit(review: ParsedReview, event: str = "COMMENT", dry_run: bool = False) -> None:
    if dry_run:
        print(diff(review, event))
        return

    gh = get_client()
    repo = gh.get_repo(review.metadata.repo)
    pr = repo.get_pull(review.metadata.pr_number)

    # Check for head SHA drift
    if pr.head.sha != review.metadata.head_sha:
        print(
            f"Warning: PR has been updated since fetch. "
            f"Head SHA was {review.metadata.head_sha[:8]}, now {pr.head.sha[:8]}."
        )

    # Submit replies
    for reply in review.replies:
        try:
            pr.create_review_comment_reply(reply.comment_id, reply.body)
            print(f"Replied to comment #{reply.comment_id}")
        except GithubException as e:
            print(f"Failed to reply to comment #{reply.comment_id}: {e}")

    # Submit new review with inline comments
    if review.new_comments or review.review_body:
        comments: list[ReviewComment] = []
        for c in review.new_comments:
            comment = ReviewComment(
                path=c.path,
                body=c.body,
                line=c.line,
                side="RIGHT",
            )
            if c.start_line:
                comment["start_line"] = c.start_line
                comment["start_side"] = "RIGHT"
            comments.append(comment)

        try:
            pr.create_review(
                body=review.review_body or "",
                event=event,
                comments=comments,
            )
            print(f"Submitted review ({event}) with {len(comments)} inline comments")
        except GithubException as e:
            print(f"Failed to submit review: {e}")
