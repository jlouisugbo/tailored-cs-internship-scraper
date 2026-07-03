import hashlib
from dataclasses import dataclass


@dataclass
class Job:
    company: str
    title: str
    url: str
    location: str
    source: str        # "greenhouse" | "lever" | "ashby" | "github_repo"
    category: int      # 0 = github_repo source, 1–3 = company category
    discovered_at: str # ISO 8601 UTC

    @property
    def id(self) -> str:
        raw = f"{self.company}:{self.title}:{self.url}"
        return hashlib.sha256(raw.encode()).hexdigest()
