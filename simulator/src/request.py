from datetime import datetime
import json
from src.utils.redis import RedisConnection
import uuid


class Request:

    # ====== Constructors
    def __init__(
        self,
        arrival_time: datetime,
        model: str,  # model identifier
        expected_machine_type: str,
        sla_time_seconds: int,
        continuous_batching_support: bool = False,
        input_tokens: int = -1,
        output_tokens: int = -1,
    ):
        self.id = uuid.uuid4().int
        self.arrival_time: datetime = arrival_time
        self.model: str = model
        self.expected_machine_type: str = expected_machine_type
        self.sla_time_seconds = sla_time_seconds
        self.continuous_batching_support: bool = continuous_batching_support
        self.input_tokens: int = input_tokens
        self.output_tokens: int = output_tokens
        self.start_time: datetime = None
        self.finish_time: datetime = None

    async def update_to_redis(self):
        async with RedisConnection() as r:
            await r.set(f"req_{self.id}", json.dumps(self.__dict__,
                                                     default=str))
            # await r.set(f"model_{self.model}", (self.sla_time_seconds, self.continuous_batching_support))
            await r.set(f"model_{self.model}", json.dumps({
                "sla_time_seconds": self.sla_time_seconds,
                "continuous_batching_support": self.continuous_batching_support
            }))

    async def update_from_redis(self):
        async with RedisConnection() as r:
            req = await r.get(f"req_{self.id}")
        self.__dict__ = json.loads(req.decode('utf-8'))

    # ====== Comparators
    def __lt__(self, other):
        return self.arrival_time < other.arrival_time

    def __gt__(self, other):
        return self.arrival_time > other.arrival_time

    def __le__(self, other):
        return self.arrival_time <= other.arrival_time

    def __ge__(self, other):
        return self.arrival_time >= other.arrival_time

    def __eq__(self, other):
        return self.arrival_time == other.arrival_time

    def __repr__(self) -> str:
        return str(self.__dict__)

    def __str__(self) -> str:
        return self.__repr__()
