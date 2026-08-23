from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    source: str
    region: str  # india | eu | infopark | uae
    sponsorship: bool
    posted_at: str | None = None  # YYYY-MM-DD when known
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SourceError:
    source: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"source": self.source, "message": self.message}
