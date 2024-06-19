from typing import Callable
from datetime import datetime, timedelta


class Task:

    # ====== Constructors
    def __init__(self, name: str, model: str, start_time: datetime,
                 deadline: datetime):
        self.name = name
        self.model = model
        self.start_time = start_time
        self.deadline = deadline

    def ended(self) -> bool:
        return datetime.now() > self.deadline
