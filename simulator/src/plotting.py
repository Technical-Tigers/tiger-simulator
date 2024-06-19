import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
import matplotlib.ticker as ticker
from matplotlib.collections import PolyCollection
import math
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple

from .request import Request
from .request_pool import RequestPool
from .utils.loading import get_models_list
from .utils.logger import Logger

RESULTS_DIR = "../results"  # TODO: move somewhere else
MACHINE_USAGE_DIR = "machine_usage"


def create_directory(directory: str):
    if not os.path.exists(directory):
        os.makedirs(directory)


def save_plot(filename):
    filepath = os.path.join(RESULTS_DIR, filename)
    Logger.info('Saving %s plot', filepath)
    plt.savefig(filepath)
    plt.clf()


def get_plot_filepath(filename):
    return os.path.join(RESULTS_DIR, filename)


def plot_trace_histogram(invocations_per_minute, div=60):
    plot_data = []
    for minute, invocations in enumerate(invocations_per_minute):
        plot_data.extend([minute // div] * invocations)
    bins = (len(invocations_per_minute) - 1) // div + 1
    plt.hist(plot_data, bins=bins, color='skyblue', edgecolor='black')
    plt.title('Invocations per minute')
    plt.xlabel(f'Time (sampled every {div} minutes)')
    plt.ylabel('Invocations')
    plt.grid(True)
    save_plot('trace.png')


def plot_workload_distribution(model_assignments):
    columns = [model.split('+')[-1] for model in model_assignments.keys()]
    values = [sum(trace) for trace in model_assignments.values()]

    plt.barh(columns, values)
    plt.subplots_adjust(left=0.3)
    plt.xlabel('Total number of invocations')
    plt.ylabel('Model')
    save_plot('workload_distribution.png')


def plot_arrival_times(simulation_start_time, arrival_times):
    plt.figure()
    t0 = simulation_start_time
    arrival_times = [(t - t0).total_seconds() for t in arrival_times]
    plt.hist(arrival_times, bins=30, color='skyblue', edgecolor='black')
    plt.title('Request arrival times')
    plt.xlabel('Arrival Time (s)')
    plt.ylabel('Frequency')
    plt.grid(True)
    save_plot('arrival_times.png')


def plot_arrival_times_dist(requests: RequestPool):
    plt.figure()
    arrival_times = [req.arrival_time.timestamp() for req in requests]
    arrival_times = [
        arrival_time - min(arrival_times) for arrival_time in arrival_times
    ]
    bins = math.ceil(len(arrival_times) / 10)

    plt.hist(arrival_times, bins=bins, color='blue', edgecolor='black')
    plt.xlabel('Arrival Times (in seconds)')
    plt.ylabel('Frequency')
    plt.title('Request arrival times distribution')

    current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    save_plot(f'request_arrivals_{current_date}.png')


def plot_avg_jct(requests: List[Request]):
    plt.figure()
    completion_times = [(request.finish_time - request.arrival_time).seconds
                        for request in requests]
    waiting_times = [(request.start_time - request.arrival_time).seconds
                     for request in requests]
    average_completion_time = sum(completion_times) / len(completion_times)
    average_waiting_time = sum(waiting_times) / len(waiting_times)

    plt.bar(["Average Job Completion Time"], [average_completion_time],
            color='blue',
            edgecolor='black')
    plt.bar(["Average Job Waiting Time"], [average_waiting_time],
            color='blue',
            edgecolor='black')
    plt.ylabel('Time')
    plt.title('Average Job Completion and Waiting Times')

    current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    save_plot(f'avg_jct_{current_date}.png')


def plot_sla_violations(requests: List[Request]):
    plt.figure()
    completion_times = [(request.finish_time - request.arrival_time).seconds
                        for request in requests]
    deadlines = [request.sla_time_seconds for request in requests]
    violations = [(d < t) for t, d in zip(completion_times, deadlines)]
    violations_percentage = sum(violations) / len(violations)

    plt.bar(["SLA violation"], [violations_percentage],
            color='blue',
            edgecolor='black')
    plt.ylabel('Percentage of SLA violation')
    plt.title('SLA violation')

    current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    save_plot(f'sla_violations_{current_date}.png')


def plot_metrics(requests: List[Request]):
    plot_avg_jct(requests)
    plot_sla_violations(requests)


def plot_cdf(requests: RequestPool):
    plt.figure()
    completion_times = [(request.finish_time - request.arrival_time).seconds
                        for request in requests]

    completion_times.sort()
    y = np.arange(len(completion_times)) / float(len(completion_times) - 1)
    plt.plot(completion_times, y)
    plt.xlabel('Completion Time (in seconds)')
    plt.ylabel('CDF')
    plt.title('CDF of Job Completion Times')

    current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    save_plot(f'cdf_{current_date}.png')


def plot_stats(machine: str, stats: List[Tuple[str, str]]):
    Logger.info("-------Summary of machine %s-------", machine)
    Logger.info(stats)
    if stats == []:
        return

    plt.figure()

    current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    load_data, infer_data = [], []
    loading_data = []
    load_dict, infer_dict = {}, {}

    simulation_time = datetime.strptime(
        stats[-1][1], '%Y-%m-%d %H:%M:%S.%f') - datetime.strptime(
            stats[0][1], '%Y-%m-%d %H:%M:%S.%f')
    simulation_time = simulation_time.total_seconds()
    min_bar_width = simulation_time / 250

    for (event_str, timestamp_str) in stats:
        model, event = event_str.split('#')
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
        if event == "load_start":
            load_dict[model] = timestamp
        elif event == "load_end":
            load_start_timestamp = load_dict[model]
            loading_data.append(
                (load_start_timestamp + timedelta(seconds=min_bar_width),
                 timestamp + timedelta(seconds=min_bar_width), model))
            load_dict[model] = timestamp
        elif event == "unload":
            load_timestamp = load_dict[model]
            load_dict.pop(model)
            load_data.append(
                (load_timestamp, timestamp + timedelta(seconds=min_bar_width),
                 model))
        elif event == "inference_start":
            infer_dict[model] = timestamp
        elif event == "inference_end":
            start_timestamp = infer_dict[model]
            infer_dict.pop(model)
            infer_data.append(
                (start_timestamp, timestamp + timedelta(seconds=min_bar_width),
                 model))
        else:
            assert (False)

    # for models that were not unloaded
    timestamp = datetime.now()
    for model in load_dict:
        load_timestamp = load_dict[model]
        load_data.append(
            (load_timestamp, timestamp + timedelta(seconds=1), model))

    models = get_models_list()
    cats = {model: (id + 1) for id, model in enumerate(models)}
    colormapping = {
        model: mcolors.to_rgba(f"C{id}") for id, model in enumerate(models)
    }
    colormapping_loading = {
        model: mcolors.to_rgba(f"C{id}", alpha=0.3)
        for id, model in enumerate(models)
    }
    verts = []
    colors = []

    start_time = min(min([d[0] for d in loading_data], default=timestamp),
                     min([d[0] for d in load_data], default=timestamp),
                     min([d[0] for d in infer_data], default=timestamp))

    loading_data = [((d[0] - start_time).total_seconds(),
                     (d[1] - start_time).total_seconds(), d[2])
                    for d in loading_data]
    load_data = [((d[0] - start_time).total_seconds(),
                  (d[1] - start_time).total_seconds(), d[2]) for d in load_data]
    infer_data = [((d[0] - start_time).total_seconds(),
                   (d[1] - start_time).total_seconds(), d[2])
                  for d in infer_data]

    for d in loading_data:
        v = [(d[0], cats[d[2]] - .4), (d[0], cats[d[2]] + .4),
             (d[1], cats[d[2]] + .4), (d[1], cats[d[2]] - .4),
             (d[0], cats[d[2]] - .4)]
        verts.append(v)
        colors.append(colormapping_loading[d[2]])

    for d in load_data:
        v = [(d[0], cats[d[2]] - .4), (d[0], cats[d[2]] + .4),
             (d[1], cats[d[2]] + .4), (d[1], cats[d[2]] - .4),
             (d[0], cats[d[2]] - .4)]
        verts.append(v)
        colors.append(colormapping[d[2]])

    for d in infer_data:
        v = [(d[0], cats[d[2]] - .2), (d[0], cats[d[2]] + .2),
             (d[1], cats[d[2]] + .2), (d[1], cats[d[2]] - .2),
             (d[0], cats[d[2]] - .2)]
        verts.append(v)
        colors.append('k')

    bars = PolyCollection(verts, facecolors=colors)

    fig, ax = plt.subplots()
    ax.add_collection(bars)
    ax.autoscale()
    loc = mdates.MinuteLocator(byminute=[0, 1, 2, 3])
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(loc))

    max_time = max(d[1] for d in loading_data + load_data + infer_data)
    Logger.info("min time: %s, max time: %s", start_time, max_time)
    xticks = np.arange(0, max_time, max_time / 10)
    ax.set_xticks(xticks)

    formatter = ticker.FuncFormatter(lambda x, pos: f'{int(x)}')
    ax.xaxis.set_major_formatter(formatter)

    ax.set_yticks(list(range(1, len(models) + 1)))
    ax.set_yticklabels(models)

    plt.subplots_adjust(left=0.3)

    create_directory(os.path.join(RESULTS_DIR, MACHINE_USAGE_DIR))
    path = os.path.join(MACHINE_USAGE_DIR,
                        f'machine_usage_{current_date}_{machine}')

    save_plot(path)
