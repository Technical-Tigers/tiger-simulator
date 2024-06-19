import logging
from datetime import datetime
from .request import Request
# from aiohttp import ClientSession
import aiohttp

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')

SCHEDULER_IP = '127.0.0.1:7270'
KUBERNETES_IP = '127.0.0.1:2138'

log = logging.getLogger(__name__)


async def schedule(req: Request) -> str:
    #   log.info(f'Sending request at {datetime.now()}: {req}')
    timeout = aiohttp.ClientTimeout(total=0,
                                    connect=0,
                                    sock_connect=0,
                                    sock_read=0)
    async with aiohttp.ClientSession() as s:
        async with s.post(
                f'http://{SCHEDULER_IP}/schedule_request/{req.id}/{req.model}/{req.expected_machine_type}',
                json={"sla": 10},
                timeout=timeout) as r:
            if r.status == 200:
                ip = await r.text()
                req.start_time = datetime.now()
                async with s.post(
                        f'http://{KUBERNETES_IP}/inference/{ip}/{req.id}',
                        timeout=timeout) as r:
                    if r.status == 200:
                        req.finish_time = datetime.now()
                        return await r.text()
                    else:
                        return "error"
