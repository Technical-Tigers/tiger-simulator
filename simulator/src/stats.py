import matplotlib.pyplot as plt
import logging
import os
import math
import numpy as np
import json
from typing import List
from datetime import datetime
import csv
import pandas as pd

from .request import Request
from .request_pool import RequestPool
from src.utils.redis import RedisConnection
from .plotting import plot_arrival_times_dist, plot_metrics, plot_cdf, plot_stats

log = logging.getLogger(__name__)

LOGS_DIR = "../logs"
REQUESTS_DIR = "../requests"
# get env variable SCHEDULER_NAME
SCHEDULER_NAME = os.getenv('SCHEDULER_NAME', 'default')


def save_logs(logs, filename: str):
    filepath = os.path.join(LOGS_DIR, filename)
    print(f'Saving {filepath} log', flush=True)

    with open(filepath, mode='w') as file:
        for item in logs:
            file.write(','.join(item) + '\n')


def save_requests(requests: List[Request], filename: str):
    os.makedirs(REQUESTS_DIR, exist_ok=True)
    filepath = os.path.join(REQUESTS_DIR, filename)
    print(f'Saving {filepath} requests', flush=True)

    df = pd.DataFrame([req.__dict__ for req in requests])
    print("-------Requests-------")
    print(df.head())
    df.to_csv(filepath, index=False)


async def generate_stats(requests: List[Request]):
    log.info("-------Summary of requests-------")
    log.info(requests)
    plot_arrival_times_dist(requests)
    plot_metrics(requests)
    plot_cdf(requests)

    current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    save_requests(requests, f'requests_{SCHEDULER_NAME}_{current_date}.csv')

    async with RedisConnection() as r:
        pod_ids = list(map(int, await r.smembers('pod_ids')))
        for id in pod_ids:
            pod_info = json.loads((await r.get(f'pod_{id}')).decode('utf-8'))
            pod_stats = pod_info.get('stats', [])
            save_logs(pod_stats,
                      f'machine_{id}_{current_date}_{SCHEDULER_NAME}.csv')
            plot_stats(id, pod_stats)
