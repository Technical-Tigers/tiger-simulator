from queue import PriorityQueue
from .request import Request
from typing import Optional


class RequestQueue:

    # ====== Constructors
    def __init__(self, max_size: int = 100000):
        self.queue: PriorityQueue = PriorityQueue(maxsize=max_size)

    # ====== Public methods
    def add_request(self, request: Request):
        self.queue.put(request)

    def empty(self):
        return self.queue.empty()

    def size(self):
        return self.queue.qsize()

    # Return item from queue
    def front(self) -> Optional[Request]:
        if self.queue.empty():
            return None
        return self.queue.queue[0]

    # Remove and return item from queue
    def pop(self) -> Optional[Request]:
        if self.queue.empty():
            return None
        return self.queue.get()
