import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.kubernetes import handle_check_deployments, handle_inference,\
  handle_check_pods, handle_namespace_request, load_model, handle_patch_namespace_request
from src.config import load_config
from src.utils.logger import set_log_level
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    await load_config()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/apis/apps/v1/deployments")
async def deployments():
    return await handle_check_deployments()


@app.get("/api/v1/pods")
async def pods(watch: bool = False):
    return await handle_check_pods()


@app.post("/preload/{machine_ip}/{tracking_id}/{model}")
async def pods(machine_ip: str,
               tracking_id: str,
               model: str,
               replace: str = None):
    return await load_model(machine_ip, tracking_id, model, replace)


@app.post("/inference/{ip}/{id}")
async def inference(ip: str, id: int):
    ip = json.loads(ip)["ip"]
    pod_id = int(ip.split(":")[0])

    return await handle_inference(pod_id, id)


@app.get("/apis/apps/v1/namespaces/default/deployments/{name}")
async def get_namespace(name: str):
    return await handle_namespace_request(name)


@app.patch("/apis/apps/v1/namespaces/default/deployments/{name}")
async def patch_namespace(name: str,
                          pretty: bool = False,
                          dryRun: bool = False,
                          patch: dict = None):
    return await handle_patch_namespace_request(name, patch)

if __name__ == "__main__":
    log_level = set_log_level()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=2138,
        log_level= log_level,
    )
