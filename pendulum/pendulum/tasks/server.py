from datetime import datetime
import os
import socket
import subprocess
import time

from celery import chain, chord
from celery.exceptions import Reject
import numpy as np

import pendulum as ebi
from ..app import app
from .worker import simulate_pendulum_instance


## Monitoring tasks

@app.task
def monitor_queues(ignore_result=True):
    server_name = app.conf.MONITORING_SERVER_NAME
    server_port = app.conf.MONITORING_SERVER_PORT
    metric_prefix = app.conf.MONITORING_METRIC_PREFIX

    queues_to_monitor = ('server', 'worker')

    output = subprocess.check_output('rabbitmqctl -q list_queues name messages consumers', shell=True)
    lines = (line.split() for line in output.splitlines())
    data = ((queue, int(tasks), int(consumers)) for queue, tasks, consumers in lines if queue in queues_to_monitor)

    timestamp = int(time.time())
    metrics = []
    for queue, tasks, consumers in data:
        metric_base_name = "%s.queue.%s." % (metric_prefix, queue)

        metrics.append("%s %d %d\n" % (metric_base_name + 'tasks', tasks, timestamp))
        metrics.append("%s %d %d\n" % (metric_base_name + 'consumers', consumers, timestamp))

    sock = socket.create_connection((server_name, server_port), timeout=10)
    sock.sendall(''.join(metrics))
    sock.close()


## Recording the experiment status

def get_experiment_status_filename(status):
    return os.path.join(app.conf.STATUS_DIR, status)


def get_experiment_status_time():
    """Get the current local date and time, in ISO 8601 format (microseconds and TZ removed)"""
    return datetime.now().replace(microsecond=0).isoformat()


@app.task
def record_experiment_status(status):
    with open(get_experiment_status_filename(status), 'w') as fp:
        fp.write(get_experiment_status_time() + '\n')


## Seeding the computations


def parametric_sweep(theta_resolution, tmax, dt):
    # Pendulum rod lengths (m), bob masses (kg).
    L1, L2 = 1.0, 1.0
    m1, m2 = 1.0, 1.0

    # Maximum time, time point spacings (all in s).
    # tmax, dt = 30.0, 0.01

    theta1_inits = np.linspace(0, 2 * np.pi, theta_resolution)
    theta2_inits = np.linspace(0, 2 * np.pi, theta_resolution)

    import itertools
    t1t2_inits = itertools.product(theta1_inits, theta2_inits)
    return ((L1, L2, m1, m2, tmax, dt, t1t2_i[0], t1t2_i[1]) for t1t2_i in t1t2_inits)


@app.task
def seed_computations(ignore_result=True):
    # if os.path.exists(get_experiment_status_filename('started')):
    #     raise Reject('Computations have already been seeded!')

    record_experiment_status.si('started').delay()

    t_max = app.conf.T_MAX
    dt = app.conf.DT
    theta_resolution = app.conf.THETA_RESOLUTION

    chord(
        (
            simulate_pendulum_instance.s(L1, L2, m1, m2, tmax, dt, theta1_init, theta2_init)
            for (L1, L2, m1, m2, tmax, dt, theta1_init, theta2_init) in
            parametric_sweep(theta_resolution, t_max, dt)
        ),
        store_computed.s()
    ).delay()


@app.task
def store_computed(results):
    import logging
    filename = os.path.join(app.conf.RESULTS_DIR, 'results.csv')

    import csv
    with open(filename, 'wb') as csvfile:
        spamwriter = csv.writer(csvfile)
        spamwriter.writerow(['theta1_init', 'theta2_init',
                             'theta1',
                             'theta2',
                             'x1',
                             'y1',
                             'x2',
                             'y2'])
        for result in results:
            logging.warn("------------------------ %s", result[2])
            theta1_init, theta2_init,ostatak = result
            theta1, theta2, x1, y1, x2, y2 = ostatak
            # logging.warn("Line: <-%s, %s, %s, %s, %s, %s, %s, %s", theta1_init, theta2_init, theta1[-1], theta2[-1],
                         # x1[-1], y1[-1], x2[-1], y2[-1])
            spamwriter.writerow([theta1_init,
                                 theta2_init,
                                 theta1[-1],
                                 theta2[-1],
                                 x1[-1],
                                 y1[-1],
                                 x2[-1],
                                 y2[-1]])
