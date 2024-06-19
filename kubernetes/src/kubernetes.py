import json
from time import sleep
from typing import List
from datetime import datetime
import aiohttp
import asyncio
from redis import Redis

from src.utils.estimation import estimate_inference, estimate_loading
from src.deployment import Deployment
from src.utils.redis import RedisConnection
from src.pod import V1Pod, PodList
import logging

SCHEDULER_IP = '127.0.0.1:7270'


async def handle_check_deployments():
    pods = await get_deployments()
    return {"items": pods}


async def handle_check_pods():
    pods = await get_pods()
    return PodList(pods)


async def load_model(machine_ip: str,
                     tracking_id: str,
                     model: str,
                     replace: str = None):
    try:
        machine = await V1Pod.init_from_redis(machine_ip)

        model_type = model.split('+')[-1]
        replace_list = replace.split(',') if replace else []

        replace_list_types = [m.split('+')[-1] for m in replace_list]
        print(
            f"[{machine_ip}] Loading model {model}"
            f" (replacing {replace_list_types})",
            flush=True)
        print(
            f"[{machine_ip}] Models already loaded: {[m.split('+')[-1] for m in machine.models]}"
        )

        load_time = estimate_loading(model_type, machine)
        await machine.loadModel(model_type, load_time, replace_list)

        loaded_models = [m.split('+')[-1] for m in machine.models]
        print(
            f"[{machine_ip}] Model loaded: {model} in {load_time} seconds.\n"
            f"[{machine_ip}] All loaded models: {loaded_models}.",
            flush=True)

        return True
    except Exception as e:
        logging.error(f"[{machine_ip}] Failed to load model: {e}")
        return False


async def handle_inference(pod_id: int, id: int):
    pod: V1Pod = await V1Pod.init_from_redis(pod_id)

    async with RedisConnection() as r:
        req = json.loads((await r.get(f"req_{id}")).decode('utf-8'))

    print(f"Starting inference on pod {pod_id}, request: {req}", flush=True)

    # model is in the form organization_id+deployment_id+machine_type+model_type
    model_type = req["model"].split("+")[-1]
    inference_time = estimate_inference(id, pod, model_type)
    await pod.inference(model_type, inference_time)

    async with aiohttp.ClientSession() as s:
        await s.post(
            f'http://{SCHEDULER_IP}/finish_request/{id}/{pod.metadata.labels["instance_type"]}'
        )

    return "Inference completed"


async def handle_namespace_request(name: str):
    deployments = await get_deployments()
    for dep in deployments:
        if dep.metadata.name == name:
            return dep


async def handle_patch_namespace_request(name: str, patch: dict):
    deployments = await get_deployments()

    for dep in deployments:
        if dep.metadata.name == name:
            await dep.patch(patch)


async def get_deployments() -> list[Deployment]:
    async with RedisConnection() as r:
        dep_ids: set[str] = (await r.smembers("dep_ids"))

    deployments = [
        Deployment.init_from_redis(int(dep_id)) for dep_id in dep_ids
    ]
    return await asyncio.gather(*deployments)


async def get_pods() -> list[V1Pod]:
    async with RedisConnection() as r:
        pod_ids: set[str] = (await r.smembers("pod_ids"))

    pods = [V1Pod.init_from_redis(int(pod_id)) for pod_id in pod_ids]
    return await asyncio.gather(*pods)


async def start_pod(id: int):
    pod: V1Pod = await V1Pod.init_from_redis(id)
    # await pod.load()
    await pod.start()
    # TODO: state - "staring" and delay (could just make it look like work is being done)
    pass


async def halt_pod(id: int):
    pod: V1Pod = await V1Pod.init_from_redis(id)
    await pod.halt()
    # TODO: Check if idle and probably also takes time
    pass


def simulate_pods():
    while True:
        sleep(1)
        pods: list[Deployment] = None  # TODO: get from redis
        # for p in pods:
        #   p.check_status()
