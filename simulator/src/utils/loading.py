import os
import pandas as pd

BENCHMARKS_DIR = "../benchmarks"
MACHINE_TYPES = ["c5.18xlarge"]


def get_models_list():
    # benchmarks_path = os.path.join(BENCHMARKS_DIR, "dnn_latency.csv")
    # benchmarks_data = pd.read_csv(benchmarks_path)

    # models = list(set(benchmarks_data['Model']))
    # models.sort()
    models = ["0.5-llama_7B-conv",
            "0.5-llama_7B-code",
            "1-llama_7B-conv",
            "1-llama_7B-code",
            "1.5-llama_7B-conv",
            "1.5-llama_7B-code"]

    return models
