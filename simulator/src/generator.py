import os
import numpy as np
import pandas as pd
from functools import partial
from datetime import datetime, timedelta

from .request import Request
from .request_queue import RequestQueue
from .request_pool import RequestPool
from .plotting import plot_workload_distribution, plot_arrival_times
from .utils.logger import Logger

MACHINE_TYPES = ["c5.18xlarge"]
BENCHMARKS_DIR = "../../benchmarks"
LATENCIES = pd.read_csv(os.path.join(BENCHMARKS_DIR, "dnn_latency.csv"))
model_to_deadline = {}


def add_deadline(model, instance):
    if model not in model_to_deadline:
        # model_to_deadline[model] = np.random.randint(5, 10)
        model_to_deadline[model] = ((np.random.random() / 2) + 0.5) + LATENCIES[
            (LATENCIES["Model"] == model.split('+')[-1]) &
            (LATENCIES["Instance"] == instance
            )]["Latency (ms)"].values[0] / 1000 * 2


async def add_request(request: Request, request_queue: RequestQueue,
                      request_pool: RequestPool):
    await request.update_to_redis()
    request_queue.add_request(request)
    request_pool.add_request(request)


async def generate_synthetic_workload(request_queue: RequestQueue,
                                      request_pool: RequestPool,
                                      num_requests: int):
    t = 0
    stream_interval = 1000
    np_random = np.random.RandomState()
    for _ in range(num_requests):
        t += int(np_random.exponential(stream_interval))
        request = Request(arrival_time=datetime.now() +
                          timedelta(milliseconds=t),
                          model="LlaMA",
                          expected_machine_type="c5.18xlarge",
                          input_tokens=12,
                          output_tokens=34)
        await add_request(request, request_queue, request_pool)


DATA_DIR = "../data"  # TODO: move somewhere else
BENCHMARKS_DIR = "../benchmarks"


def parse_azure_llm_trace(path):
    df = pd.read_csv(path, parse_dates=["TIMESTAMP"])
    df["TIMESTAMP"] = pd.to_datetime(df["TIMESTAMP"])
    data = df.to_dict('records')
    return data


async def add_azure_llm_requests(data, request_queue: RequestQueue,
                                 request_pool: RequestPool, start_time,
                                 finish_time):
    for row in data:
        timestamp = row["TIMESTAMP"]

        if timestamp < start_time:
            continue
        if timestamp > finish_time:
            break

        request = Request(timestamp, "LlaMa2-7b", "c5.18xlarge",
                          row["ContextTokens"], row["GeneratedTokens"])
        await add_request(request, request_queue, request_pool)


async def generate_azure_llm_workload(request_queue: RequestQueue,
                                      request_pool: RequestPool,
                                      trace_length_mins: int = 60):
    llm_code_path = os.path.join(DATA_DIR, "llm",
                                 "AzureLLMInferenceTrace_code.csv")
    llm_code_data = parse_azure_llm_trace(llm_code_path)

    llm_conv_path = os.path.join(DATA_DIR, "llm",
                                 "AzureLLMInferenceTrace_conv.csv")
    llm_conv_data = parse_azure_llm_trace(llm_conv_path)

    time_delta = timedelta(minutes=trace_length_mins)
    start_time = max(llm_code_data[0]["TIMESTAMP"],
                     llm_conv_data[0]["TIMESTAMP"])
    end_time = min(llm_code_data[-1]["TIMESTAMP"],
                   llm_conv_data[-1]["TIMESTAMP"])
    duration = end_time - start_time

    if duration > time_delta:
        random_delay = np.random.uniform(0, (duration - time_delta).seconds())
    else:
        random_delay = 0
    random_delay = timedelta(seconds=random_delay)

    await add_azure_llm_requests(llm_code_data, request_queue, request_pool,
                                 start_time + random_delay,
                                 start_time + random_delay + time_delta)
    await add_azure_llm_requests(llm_conv_data, request_queue, request_pool,
                                 start_time + random_delay,
                                 start_time + random_delay + time_delta)


# Returns DataFrame with trace_length_mins bins.
def get_azure_functions_data(data_path, trace_length_mins):
    df = pd.read_csv(data_path)
    TOTAL_MINUTES = 60 * 24
    start_min = np.random.randint(0, TOTAL_MINUTES - trace_length_mins)
    minutes = [start_min + delta for delta in range(0, trace_length_mins)]
    df = df.iloc[:, minutes]
    return df


def get_function_trace(df, function_id):
    return df.iloc[function_id].tolist()[:]


# Returns dictionary from model name to df with one-minute bins.
def assign_traces_to_models(data, benchmark_models, model_to_assignments):
    assignments = {}
    Logger.info("model to function_ids:")
    for model in benchmark_models:
        num_traces = model_to_assignments(model)
        function_ids = np.random.randint(0, len(data), size=num_traces)
        Logger.info('%s: %s', model, function_ids)
        traces = list(map(partial(get_function_trace, data), function_ids))
        assignments[model] = [sum(invocations) for invocations in zip(*traces)]
    return assignments


def random_process_generator(time_span_ms, events):
    return map(int, np.random.randint(0, time_span_ms, size=events))


def poisson_process_generator(time_span_ms, events):
    # TODO
    pass

async def add_azure_functions_requests(simulation_start_time: datetime,
                                       model: str, trace,
                                       arrival_time_generator,
                                       request_queue: RequestQueue,
                                       request_pool: RequestPool,
                                       input_tokens_gen,
                                       output_tokens_gen):
    Logger.info('trace len: %d', len(trace))
    add_deadline(model, "c5.18xlarge")
    for minute, bin in enumerate(trace):
        deltas_ms = arrival_time_generator(
            60 * 1000,  # one minute
            bin)
        for delta_ms in deltas_ms:
            delta = timedelta(milliseconds=delta_ms)
            timestamp = simulation_start_time \
                        + timedelta(minutes=minute) \
                        + delta
            request = Request(timestamp, model, "c5.18xlarge",
                              model_to_deadline[model],
                              float(model.split('-')[0].split('+')[-1]) >= 1,
                              input_tokens=input_tokens_gen(model),
                              output_tokens=output_tokens_gen(model))
            await add_request(request, request_queue, request_pool)

token_data = {}
def get_input_tokens(model: str):
    scale, name, type = model.split('-')
    return token_data[type] \
                     [np.random.randint(0, \
                                        len(token_data[type]))] \
                     ["ContextTokens"]

def get_output_tokens(model: str):
    scale, name, type = model.split('-')
    return token_data[type] \
                     [np.random.randint(0, \
                                        len(token_data[type]))] \
                     ["GeneratedTokens"]

async def generate_azure_functions_workload(request_queue: RequestQueue,
                                            request_pool: RequestPool,
                                            workload: str,
                                            trace_length_mins: int = 60):
    DAY = '07'  # from ['01', ..., '14']
    filename = f'invocations_per_function_md.anon.d{DAY}.csv'
    data_path = os.path.join(DATA_DIR, "functions", filename)
    Logger.info('Loading Azure Functions workload from %s.', data_path)
    azure_data = get_azure_functions_data(data_path, trace_length_mins)

    input_tokens_gen = lambda x: -1
    output_tokens_gen = lambda x: -1

    if workload == "DNN":
        benchmarks_path = os.path.join(BENCHMARKS_DIR, "dnn_latency.csv")
        Logger.info('Loading benchmarks from %s', benchmarks_path)
        benchmarks_data = pd.read_csv(benchmarks_path)

        # filter instances that are in MACHINE_TYPES
        benchmarks_data = benchmarks_data[benchmarks_data['Instance'].isin(
            MACHINE_TYPES)]

        benchmarks_data['Full_name'] = "1+1+1+" + benchmarks_data[
            'Instance'] + "+" + benchmarks_data['Model']

        models = list(set(benchmarks_data['Full_name']))
        models.sort()

    elif workload == "LLM":
        llm_models = [
            "0.5-llama_7B-conv",
            "0.5-llama_7B-code",
            "1-llama_7B-conv",
            "1-llama_7B-code",
            "1.5-llama_7B-conv",
            "1.5-llama_7B-code"
        ]
        models = []
        for model in llm_models:
            models.append("1+1+1" + "+c5.18xlarge+" + model)
        for model in models:
            if model.endswith("conv"):
                model_to_deadline[model] = 10
            else:
                model_to_deadline[model] = 5
        llm_code_path = os.path.join(DATA_DIR, "llm",
                                    "AzureLLMInferenceTrace_code.csv")
        token_data["code"] = parse_azure_llm_trace(llm_code_path)

        llm_conv_path = os.path.join(DATA_DIR, "llm",
                                    "AzureLLMInferenceTrace_conv.csv")
        token_data["conv"] = parse_azure_llm_trace(llm_conv_path)

        input_tokens_gen = get_input_tokens
        output_tokens_gen = get_output_tokens
    else:
        assert(False)

    model_to_trace = assign_traces_to_models(azure_data, models, lambda x: 92)
    plot_workload_distribution(model_to_trace)

    simulation_start_time = datetime.now()
    for model in model_to_trace:
        await add_azure_functions_requests(simulation_start_time, model,
                                           model_to_trace[model],
                                           random_process_generator,
                                           request_queue, request_pool,
                                           input_tokens_gen,
                                           output_tokens_gen)

    arrival_times = [r.arrival_time for r in request_pool.get_requests()]
    plot_arrival_times(simulation_start_time, arrival_times)
    Logger.info("Finished generating requests")
