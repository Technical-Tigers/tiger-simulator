from src.deployment import Deployment
from src.utils.redis import RedisConnection, open_redis_connection
import json

config_path = 'config/machines.json'


def parse_json() -> list[Deployment]:
    with open(config_path, 'r') as f:
        config = json.load(f)

    deps = []
    for id, deployment_json in enumerate(config):
        dep = Deployment(id, deployment_json)
        deps.append(dep)

    return deps


async def init_deps(deployments: list[Deployment]):
    for dep in deployments:
        await dep.save()


async def load_config():
    async with RedisConnection() as r:
        await r.flushall()

    deps = parse_json()
    await init_deps(deps)
