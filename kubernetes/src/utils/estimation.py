from src.pod import V1Pod
import pandas as pd

BENCHMARKS_DIR = "../benchmarks"  # TODO: move somewhere else
LATENCIES = pd.read_csv(BENCHMARKS_DIR + "/dnn_latency.csv")
MODEL_SIZES = pd.read_csv(BENCHMARKS_DIR + "/model_sizes.csv")
LOADING_SPEED = 4096  # Mb per second


# Returns number of seconds to sleep
def estimate_loading(model: str, machine: V1Pod) -> float:
    return MODEL_SIZES[MODEL_SIZES["Model"] ==
                       model]["Size"].values[0] / LOADING_SPEED * 8


# Returns number of seconds to sleep
def estimate_inference(id: int, pod: V1Pod, model: str) -> float:
    return LATENCIES[(LATENCIES["Model"] == model) &
                     (LATENCIES["Instance"] == pod.metadata.
                      labels['instance_type'])]["Latency (ms)"].values[0] / 1000
