import numpy as np
from numpy import array
import random
from scipy import stats

# assume that we have blocks of 5 minutes
#
#
#
name_states = ["arr", "as1", "as2", "wait", "doc1", "doc2", "doc3", "home"]
arrival_prob = 1/2
see_doc_prob = 1/8


def create_matrix(p_doc: float, states: list):
    """
    creates markov matrix
    """
    r1 = array([0, 1, 0, 0, 0, 0, 0, 0])
    r2 = array([0, 0, 1, 0, 0, 0, 0, 0])
    r3 = array([0, 0, 0, p_doc, 0, 0, 0, 1-p_doc])
    r4 = array([0, 0, 0, 0, 1, 0, 0, 0])
    r5 = array([0, 0, 0, 0, 0, 1, 0, 0])
    r6 = array([0, 0, 0, 0, 0, 0, 1, 0])
    r7 = array([0, 0, 0, 0, 0, 0, 0, 1])
    r8 = array([0, 0, 0, 0, 0, 0, 0, 1])
    matrix = array([r1, r2, r3, r4, r5, r6, r7, r8])

    return matrix


def walk(current_position, matrix):
    """
    does one step of the walk of the markov chain
    """
    new_position = random.choices(np.arange(8), weights=matrix[current_position], k=1)
    return new_position


def sim(states):
    """

    """
    old_dist = np.zeros(len(states), dtype=int)
    t = 0
    matrix = create_matrix(1/8, states)
    while t < 100:
        old_dist[0] += 1
        new_dist = np.zeros(len(states), dtype=int)
        for i in range(8):
            value = old_dist[i]
            for j in range(value):
                new_pos = walk(i, matrix)
                new_dist[new_pos] += 1
        old_dist = new_dist
        t += 1
        print(t, old_dist)
    return old_dist


sim(name_states)






