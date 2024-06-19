from typing import List, Set
from time import sleep
from datetime import datetime
import aiohttp
import json
import asyncio

from .task import Task
from .request_queue import RequestQueue
from .request_pool import RequestPool
from .request import Request
from .generator import generate_synthetic_workload, generate_azure_functions_workload
from .stats import generate_stats
from .scheduler_proxy import schedule
from .utils.logger import Logger

import numpy as np

SEED = 70

class Simulator:

    # ====== Constructors
    def __init__(self):
        pass

    # ====== Public methods
    async def start(self):
        await self.__generate_requests()

        Logger.info('Starting simulation')
        tasks: Set[asyncio.Task[None]] = set()
        while not self.requests.empty():
            await asyncio.sleep(0.1)
            for req in self.__get_incoming_requests():
                task = asyncio.create_task(schedule(req))
                tasks.add(task)
                task.add_done_callback(tasks.discard)
                await asyncio.sleep(0)  #let the task start
        await asyncio.gather(*tasks)

    async def finish(self):
        await generate_stats(self.request_pool.get_requests())

    # ====== Private methods
    async def __generate_requests(self):
        # TODO: get which workload from a config
        # TODO: maybe have a Generator class that plots everything itself
        np.random.seed(SEED)
        self.requests: RequestQueue = RequestQueue()
        self.request_pool: RequestPool = RequestPool()
        # await generate_synthetic_workload(self.requests, self.request_pool, 50)
        await generate_azure_functions_workload(self.requests,
                                                self.request_pool,
                                                "LLM",
                                                30)

    def __get_incoming_requests(self) -> List[Request]:
        request_list: List[Request] = []
        while not self.requests.empty() \
              and self.requests.front().arrival_time <= datetime.now():
            request_list.append(self.requests.pop())
        return request_list
