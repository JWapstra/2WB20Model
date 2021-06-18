import numpy as np
from math import factorial as fac
import itertools
import pandas as pd

# import tables as tb



def A1_index(x: int) -> int:
    return (x // (28 * (limit_of_W + 1) * 5 * 3))


def A2_index(x: int) -> int:
    return (x // (28 * (limit_of_W + 1) * 5)) % 3


def A3_index(x: int) -> int:
    return (x // (28 * (limit_of_W + 1))) % 5


def W_index(x: int) -> int:
    return (x // 28) % (limit_of_W + 1)


def j_index(a_1, a_2, a_3, w, o):
    return o + w * 28 + a_3 * 28 * (limit_of_W + 1) + a_2 * 28 * (limit_of_W + 1) * 5 + a_1 * 28 * (
                limit_of_W + 1) * 5 * 3


def initialize_state_space():
    import itertools

    S = []

    somelists = [
        [0, 1, 2],
        [0, 1, 2],
        [0, 1, 2, 3, 4],
        list(range(limit_of_W + 1)),
        list(range(28))
    ]
    for element in itertools.product(*somelists):
        S += [element]
    S.sort()
    return S


def make_O_dictionary():
    import itertools

    S = []

    somelists = [
        [0, 1, 2],
        [0, 1, 2],
        [0, 1, 2],
        [0, 1, 2],
        [0, 1, 2],
        [0, 1, 2],
    ]
    for element in itertools.product(*somelists):
        if sum(element) < 3:
            S += [element]
    S.sort()
    return dict(zip(list(range(len(S))), S))


p = 0.5


def f(b_2: int, b_3: int, b: int, a_1: int, a_2: int, a_3: int, w: int) -> int:
    assert a_1 >= 0 and a_2 >= 0 and a_3 >= 0 and w >= 0 and b_2 >= 0 and b_3 >= 0 and b >= 0, "entries must be positive"
    assert b_3 == a_2 + a_1 - b_2 and a_1 >= b_2, "conditions are not met"

    value = (1 / 2) ** (a_1) * fac(a_1) / (fac(b_2) * fac(a_1 - b_2))

    # value *= (1/2)**a_3  #for waiting room

    sum = 0
    if b - w >= 0 and a_3 - b + w >= 0:
        if b < limit_of_W:
            sum = fac(a_3) / (fac(b - w) * fac(a_3 - b + w)) * p ** (b - w) * (1 - p) ** (a_3 - b + w)
        elif b == limit_of_W:
            for w_3 in range(a_3 + 1):
                if w_3 + w >= b:
                    sum += fac(a_3) / (fac(w_3) * fac(a_3 - w_3)) * p ** (w_3) * (1 - p) ** (a_3 - w_3)
    value *= sum

    return value


def O_prob(O1_old: int, O2_new: int) -> int:
    return (1 / 2) ** (O1_old) * fac(O1_old) / (fac(O2_new) * fac(O1_old - O2_new))


def possible_os(O_old: list):
    x = make_O_dictionary()
    x = {v: k for k, v in x.items()}
    l = []
    s = []
    for v in ((a, b, c) for a, b, c in itertools.product(range(O_old[0] + 1), range(O_old[2] + 1), range(O_old[4] + 1))
              if sum((a, b, c)) <= 2):
        O_new = [0, 0, 0, 0, 0]
        O_new[0] = O_old[0] - v[0]
        O_new[1] = v[0] + O_old[1]
        O_new[2] = O_old[2] - v[1]
        O_new[3] = v[1] + O_old[3]
        O_new[4] = O_old[4] - v[2]
        for i in range(3 - sum(O_new)):
            l += [x.get(tuple([i] + O_new))]
            s += [tuple([i] + O_new)]
    return l, s


def transition_matrix_new(b_1):
    l = len(initialize_state_space())
    P_matrix = np.zeros([l, l])
    O_thing = make_O_dictionary()
    for i in range(l):
        a_1 = A1_index(i)
        a_2 = A2_index(i)
        a_3 = A3_index(i)
        w = W_index(i)
        O_old = O_thing[i % 28]
        (O1_old, O2_old, O3_old, O4_old, O5_old, O6_old) = O_old

        for b_2 in range(a_1 + 1):
            b_3 = a_1 + a_2 - b_2
            for b in range(max(0, w-2), min(limit_of_W, w + a_3) + 1):
                for O_new_index in possible_os(O_old)[0]:
                    j = j_index(b_1, b_2, b_3, b, O_new_index)
                    O_new = O_thing[j % 28]
                    (O1_new, O2_new, O3_new, O4_new, O5_new, O6_new) = O_new
                    if O_new[1:6] in (k[1:6] for k in possible_os(list(O_old))[1]):
                        c = O_new[0]
                        if c == 2:
                            if w >= 2:
                                P_matrix[i, j] = (
                                    (O_prob(O1_old, O2_new) * O_prob(O3_old, O4_new) * O_prob(O5_old, O6_new)
                                     * f(b_2, b_3, b, a_1, a_2, a_3, w - c)))
                        elif c == 1:
                            if w == 1 and sum(O_new[1:6]) == 0:
                                P_matrix[i, j] = (
                                    (O_prob(O1_old, O2_new) * O_prob(O3_old, O4_new) * O_prob(O5_old, O6_new)
                                     * f(b_2, b_3, b, a_1, a_2, a_3, w - c)))
                            elif w >= 1 and sum(O_new[1:6]) == 1:
                                P_matrix[i, j] = (
                                    (O_prob(O1_old, O2_new) * O_prob(O3_old, O4_new) * O_prob(O5_old, O6_new)
                                     * f(b_2, b_3, b, a_1, a_2, a_3, w - c)))
                        elif c == 0:
                            if w == 0:
                                P_matrix[i, j] = (
                                    (O_prob(O1_old, O2_new) * O_prob(O3_old, O4_new) * O_prob(O5_old, O6_new)
                                     * f(b_2, b_3, b, a_1, a_2, a_3, w - c)))

                            elif w >= 1 and sum(O_new[1:6]) == 2:
                                P_matrix[i, j] = (
                                    (O_prob(O1_old, O2_new) * O_prob(O3_old, O4_new) * O_prob(O5_old, O6_new)
                                     * f(b_2, b_3, b, a_1, a_2, a_3, w - c)))

    return P_matrix



def estimated_waiting_people(P0,P1,P2):
    state_space = initialize_state_space()
    v = np.zeros(len(P0))
    v[j_index(schedule[0], 0, 0, 0, 0)] = 1
    summ = 0
    l = []
    for i in schedule[1:]:
        if i == 0:
            v = v.dot(P0)
        if i == 1:
            v = v.dot(P1)
        if i == 2:
            v = v.dot(P2)
        v = v / sum(v)
        for j in range(len(v)):
            summ += state_space[j][3] * v[j]
        v = v / np.linalg.norm(v)
        l += [summ]
        print(summ)
    return l
limit_of_W = 8
p = 0.5


import time
start_time = time.time()
P0 = transition_matrix_new(0)
print('fuori uno')
P1 = transition_matrix_new(1)
print('fuori due')
P2 = transition_matrix_new(2)
print('fuori tre')
for schedule in [itertools.product(list(range(3))*6)]*8:
    listt = []
    listt += [estimated_waiting_people(P0,P1,P2)]
print("time elapsed: {:.2f}s".format(time.time() - start_time))
table = np.array(listt)
transpose = table.T
table = transpose.tolist()
r = pd.DataFrame(table,columns =['p = 0.5'])
r.to_excel("Long schedule 4 w = 8.xlsx")


"""

schedule = [2, 1, 1, 1, 0, 0] * 8 + [0] * 6
listt = []
import time
for i in range(21):
    p = 0.05 *i
    print('p = ' + str(p))
    start_time = time.time()
    P0 = transition_matrix_new(0)
    P1 = transition_matrix_new(1)
    P2 = transition_matrix_new(2)
    listt += [estimated_waiting_people(P0,P1,P2)]
    print("time elapsed: {:.2f}s".format(time.time() - start_time))
table = np.array(listt)
transpose = table.T
table = transpose.tolist()
r = pd.DataFrame(table,columns =[(i*0.05) for i in range(21)])
r.to_excel("Schedule 5 w = 8.xlsx")


limit_of_W = 8
schedule = [1, 2, 0, 2, 0, 0] * 8 + [0] * 6
listt = []
import time
for i in range(21):
    p = 0.05 *i
    print('p = ' + str(p))
    start_time = time.time()
    P0 = transition_matrix_new(0)
    P1 = transition_matrix_new(1)
    P2 = transition_matrix_new(2)
    listt += [estimated_waiting_people(P0,P1,P2)]
    print("time elapsed: {:.2f}s".format(time.time() - start_time))
table = np.array(listt)
transpose = table.T
table = transpose.tolist()
r = pd.DataFrame(table,columns =[(i*0.05) for i in range(21)])
r.to_excel("Schedule 6 w = 8.xlsx")



limit_of_W = 8
schedule = [2, 2, 1, 0, 0, 0] * 8 + [0] * 6
listt = []
import time
for i in range(21):
    p = 0.05 *i
    print('p = ' + str(p))
    start_time = time.time()
    P0 = transition_matrix_new(0)
    P1 = transition_matrix_new(1)
    P2 = transition_matrix_new(2)
    listt += [estimated_waiting_people(P0,P1,P2)]
    print("time elapsed: {:.2f}s".format(time.time() - start_time))
table = np.array(listt)
transpose = table.T
table = transpose.tolist()
r = pd.DataFrame(table,columns =[(i*0.05) for i in range(21)])
r.to_excel("Schedule 4 w = 8.xlsx")

limit_of_W = 6
schedule = [2, 1, 1, 1, 0, 0] * 8 + [0] * 6
listt = []
import time
for i in range(21):
    p = 0.05 *i
    print('p = ' + str(p))
    start_time = time.time()
    P0 = transition_matrix_new(0)
    P1 = transition_matrix_new(1)
    P2 = transition_matrix_new(2)
    listt += [estimated_waiting_people(P0,P1,P2)]
    print("time elapsed: {:.2f}s".format(time.time() - start_time))
table = np.array(listt)
transpose = table.T
table = transpose.tolist()
r = pd.DataFrame(table,columns =[(i*0.05) for i in range(21)])
r.to_excel("Schedule 5 w = 6.xlsx")

limit_of_W = 6
schedule = [1, 2, 0, 2, 0, 0] * 8 + [0] * 6
listt = []
import time
for i in range(21):
    p = 0.05 *i
    print('p = ' + str(p))
    start_time = time.time()
    P0 = transition_matrix_new(0)
    P1 = transition_matrix_new(1)
    P2 = transition_matrix_new(2)
    listt += [estimated_waiting_people(P0,P1,P2)]
    print("time elapsed: {:.2f}s".format(time.time() - start_time))
table = np.array(listt)
transpose = table.T
table = transpose.tolist()
r = pd.DataFrame(table,columns =[(i*0.05) for i in range(21)])
r.to_excel("Schedule 6 w = 6.xlsx")
"""