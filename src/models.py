from dataclasses import dataclass
from datetime import datetime

@dataclass
class Post:
    """Represents a single forum post."""
    username: str
    date: datetime
