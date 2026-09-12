from dataclasses import dataclass
from datetime import datetime


@dataclass
class PRMetadata:
    pr_number: int
    repo: str
    title: str
    head_sha: str
    fetched_at: datetime


@dataclass
class CommentInfo:
    id: int
    path: str
    line: int
    start_line: int | None
    side: str
    body: str
    user: str
    created_at: datetime
    in_reply_to_id: int | None


@dataclass
class CommentThread:
    root: CommentInfo
    replies: list[CommentInfo]


@dataclass
class Reply:
    comment_id: int
    body: str


@dataclass
class NewComment:
    path: str
    line: int
    start_line: int | None
    body: str


@dataclass
class ParsedReview:
    metadata: PRMetadata
    review_body: str | None
    replies: list[Reply]
    new_comments: list[NewComment]
