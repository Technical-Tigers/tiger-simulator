from src.pod import V1Pod
import pandas as pd

LOADING_SPEED = 4096  # Mb per second
ONE_TOKEN_TIME = 0.0139
MODEL_SIZE = 56 * 1024  # 56 GB


# Returns number of seconds to sleep
def estimate_loading(model: str, machine: V1Pod, unloading: bool) -> float:
    if not unloading:
        return 0
    multiplier = float(model.split('-')[0])
    return multiplier * MODEL_SIZE * 8 / LOADING_SPEED


# Returns number of seconds to sleep
def estimate_inference(id: int, pod: V1Pod, model: str, tokens: int) -> float:
    multiplier = float(model.split('-')[0])
    return tokens * ONE_TOKEN_TIME * multiplier