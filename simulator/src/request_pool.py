from .request import Request
from typing import List


class RequestPool:

    # ====== Constructors
    def __init__(self, max_size: int = 100000):
        self.pool: List[Request] = []

    # ====== Public methods
    def add_request(self, request: Request):
        self.pool.append(request)

    def get_requests(self):
        return self.pool
