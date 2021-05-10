from collections import deque
from math import sqrt

import numpy as np
from numpy import array, zeros, mean, std
import random
from scipy import stats

# assume that we have blocks of 5 minutes
#
#
#
name_states = ["arr", "as1", "as2", "as3", "as4", "as5", "as6", "wait",
               "doc1", "doc2", "doc3", "doc4", "doc5", "doc6", "doc7", "doc8", "doc9", "doc10",
               "doc11", "doc12", "home"]
arrival_prob = 1/2
see_doc_prob = 1/8


class Patient:

    def __init__(self, arrive_time):
        self.loc = 0
        self.arr_time = arrive_time
        self.start_time = None
        self.wait_time = -1
        self.total_time = 0

    def __str__(self):
        return 'arr_t :'+str(self.arr_time)+' current position: '+str(self.loc)

    def update(self, new_loc):
        self.loc = new_loc

    def start_wait(self, start_time):
        self.start_time = start_time

    def end_wait(self, end_time):
        self.wait_time = end_time - self.start_time

    def time_leave(self, time):
        self.total_time = time - self.arr_time


def confidence_interval(calc_mean, calc_std, nr_observations):
    halfwidth = 1.96*calc_std/sqrt(nr_observations)
    return calc_mean-halfwidth, calc_mean+halfwidth


def create_matrix(p_doc: float, p_ass_skip: float, p_doc_skip: float, states: list, doc_available: bool):
    """
    creates markov matrix
    """
    n = len(states)
    matrix = zeros((n, n))
    for i in range(n-1):
        matrix[i][i+1] = 1
    matrix[-1][-1] = 1
    matrix[6][7] = p_doc
    matrix[6][-1] = 1-p_doc
    matrix[7][8] = doc_available
    matrix[7][7] = not doc_available
    for j in [2,4]:
        matrix[j][j+1] = 1-p_ass_skip
        matrix[j][j+2] = p_ass_skip
    for k in [9, 11, 13, 15, 17]:
        matrix[k][k + 1] = 1 - p_doc_skip
        matrix[k][k + 2] = p_doc_skip

    return matrix


def walk(current_position, matrix, length):
    """
    does one step of the walk of the markov chain
    """
    new_position = random.choices(np.arange(length), weights=matrix[current_position], k=1)[0]
    return new_position


def sim(t_schedule: int, t_max: int, p_doc: float, p_ass_skip: float, p_doc_skip: float, states: list):
    """

    """
    n = len(states)
    patients = deque()
    t = 0
    matrix_free = create_matrix(p_doc, p_ass_skip, p_doc_skip, states, doc_available=True)
    matrix_busy = create_matrix(p_doc, p_ass_skip, p_doc_skip, states, doc_available=False)
    currently_at_doc = 0
    while t < t_max:
        if (t % 2) == 0 and t < t_schedule:
            patients.append(Patient(t))
            patients.append(Patient(t))

        for patient in patients:
            if patient.loc != n-1:
                if currently_at_doc < 2:
                    new_loc = walk(patient.loc, matrix_free, n)
                elif currently_at_doc == 2:
                    new_loc = walk(patient.loc, matrix_busy, n)
                else:
                    new_loc = None
                if new_loc == n-1:
                    currently_at_doc -= 1
                    patient.time_leave(t)
                elif new_loc == 8:
                    currently_at_doc += 1
                    patient.end_wait(t)
                elif new_loc == 6:
                    patient.start_wait(t+1)
                patient.update(new_loc)
        t += 1
    return patients


def simulate(t_schedule: int, t_max: int, p_doc: float, p_ass_skip: float, p_doc_skip: float, states: list):
    results = sim(t_schedule, t_max, p_doc, p_ass_skip, p_doc_skip, name_states)
    wait_times = deque()
    total_times = deque()
    for patient in results:
        if patient.wait_time > -1:
            wait_times.append(patient.wait_time)
        total_times.append(patient.total_time)
    if len(wait_times) > 0:
        mean_wait = mean(wait_times)
    else:
        mean_wait = 0
    mean_total = mean(total_times)
    return mean_wait, mean_total


def multi_sim(nr_runs, t_schedule: int, t_max: int,
              p_doc: float, p_ass_skip: float, p_doc_skip: float, states: list):
    mean_wait_list = deque()
    mean_total_list = deque()
    for i in range(nr_runs):
        mean_wait, mean_total = simulate(t_schedule, t_max, p_doc, p_ass_skip, p_doc_skip, name_states)
        mean_wait_list.append(mean_wait)
        mean_total_list.append(mean_total)
    ci_wait = confidence_interval(mean(mean_wait_list), std(mean_wait_list), nr_runs)
    ci_total = confidence_interval(mean(mean_total_list), std(mean_total_list), nr_runs)
    return ci_wait, ci_total


def check_prop(nr_steps, step_size, states):
    if (nr_steps-1)*step_size <= 1:
        for i in range(nr_steps):
            for j in range(nr_steps):
                for k in range(nr_steps):
                    a = multi_sim(10, 108, 200, step_size*i, step_size*j, step_size*k, states)
                    print((step_size*i, step_size*j, step_size*k), a)
    else:
        print("Invalid stepsize and/or number of steps")


check_prop(6,0.2,name_states)

# multi_sim(100, 108, 200, 0.25, 0.4, 0.3, name_states)
# print(a)







