from dataclasses import dataclass
from datetime import datetime

@dataclass
class Post:
    username: str
    date: datetime
