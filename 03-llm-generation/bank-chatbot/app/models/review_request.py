from typing import TypedDict
from datetime import datetime


class ReviewRequest(TypedDict):
    request_id: str
    status: str
    requested_limit_cents: int
    current_limit_cents: int
    requires_human_follow_up: bool
    message: str
    created_at: datetime
