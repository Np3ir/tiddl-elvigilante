<<<<<<< HEAD
=======
from __future__ import annotations
>>>>>>> 51f206d9cee155d16ba05c48767a0da1772ff3c1
import re

from datetime import datetime
from pydantic import BaseModel


def normalize_review_text(text: str | None = None) -> str:
    if not text:
        return ""

    text = re.sub(
        r"\[wimpLink\b[^\]]*\](.*?)\[/wimpLink\]",
        r"\1",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    text = re.sub(r"\[/?wimpLink\b[^\]]*\]", "", text, flags=re.IGNORECASE)

    return text.strip()


class AlbumReview(BaseModel):
    source: str
    lastUpdated: datetime
    text: str
    summary: str

    def normalized_text(self) -> str:
        return normalize_review_text(self.text)
