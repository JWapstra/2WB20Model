from collections import deque, Counter
from math import sqrt
from random import random, seed
from numpy import mean, arange, array, std
from matplotlib import pyplot as plt
from scipy import stats

# seed(10)

# A1,A2,A3,W1,D1,D2,D3,D4,D5,D6, H



class BasicModel:
    def __init__(self, prob_to_doc=0.5, prob_emergency=0.04, mean_doc_arr_time=1, schedule=[]):
        self.state = [0 for i in range(0, 11)]
        self.schedule = schedule
        self.t_max = 50
        self.time = 0
        self.W1 = 3
        self.NOPTS = 2  # number of optomologists
        self.distribution = stats.geom(1/mean_doc_arr_time)

        # Visitor probabilities
        self.prob_1 = 0.5  # probability that 1 person enters building
        self.prob_2 = 0.2  # probability that 2 people enters building
        self.prob_emergency = prob_emergency  # probability of having a emergency
        # the probability that somebody has to go to the doctor after visiting one of the assistents
        self.prob_to_doc = prob_to_doc

        self.prob_skipsA2 = 0.5

        self.prob_skipsO2n = 0.5

        # Emergency state
        self.nr_emergencies = 0

    def reset_state(self):
        self.state = [0 for i in range(0, 11)]

    def skipO2n(self, li: list, fromIndex):
        """
        This is a function to shorten the code in the 'moveOPeople' function.
        It determines if a person can skip the O2n state and can skip to the O_(2n+1) state.
        """
        for _ in range(li[fromIndex]):
            skipO = random() < self.prob_skipsO2n
            if skipO:
                li[fromIndex + 2] += 1
            else:
                li[fromIndex + 1] += 1

        return li

    def moveOPeople(self, li: list):
        """
        Determines what happens to the people who are at the optomologist when 5 minutes pass.
        """
        busyOpts = sum(li[self.W1+1:-2])
        freeOpts = self.NOPTS - busyOpts

        li[10] += li[9]
        li[9] = 0

        li = self.skipO2n(li, 8)
        li[8] = 0

        li[8] += li[7]
        li[7] = 0

        li = self.skipO2n(li, 6)
        li[6] = 0

        li[6] += li[5]
        li[5] = 0

        li = self.skipO2n(li, 4)
        li[4] = 0

        # # Add the number of free optomologists to O1
        toAdd = min(freeOpts, li[3])
        li[4] += toAdd
        li[3] -= toAdd

        return li

    def moveAPeople(self, li: list):
        """
        Determines what happens to people who are at one of the assistants.

        We assume that the waiting room and the optomologists have already been handled.
        The queue starts moving at the front (aka A3 moves first)
        """

        # A3 moves to W1 or H
        for _ in range(li[2]):
            to_doc = random() < self.prob_to_doc
            if to_doc:
                li[3] += 1
            else:
                li[-1] += 1  # here they go home already
        li[2] = 0

        # A2 to A3
        li[2] += li[1]
        li[1] = 0

        # from A1 to A2 or A3
        for _ in range(li[0]):
            skipA4 = random() < self.prob_skipsA2
            if skipA4:
                li[2] += 1
            else:
                li[1] += 1
        li[0] = 0

        return li

    def visitor(self):
        if len(self.schedule)>0 and self.time <= self.t_max:
            people_to_add = self.schedule[self.time]
        else:
            r = random()
            if 0 < r <= self.prob_1:
                # Add one person
                people_to_add = 1

            elif self.prob_1 < r <= self.prob_1 + self.prob_2:
                people_to_add = 2
            else:
                people_to_add = 0
        self.state[0] = self.state[0] + people_to_add

    def check_emergency(self):

        if random() <= self.prob_emergency:
            # print("emergency")
            self.state[self.W1] += 1
            self.nr_emergencies += 1

    def round(self):
        """
        10 minutes pass
        """
        self.check_emergency()
        self.state = self.moveOPeople(self.state)
        self.state = self.moveAPeople(self.state)
        self.visitor()
        # print(self.state)

    def run(self):
        """
        Run one simulation
        """
        # Reset variables for next run
        self.reset_state()
        self.nr_emergencies = 0
        self.NOPTS = 1
        nr_waiting_patients = deque()
        arr_time = self.distribution.rvs()

        for t in range(self.t_max):
            self.time = t
            if t == arr_time:
                self.NOPTS += 1
            self.round()
            nr_waiting_patients.append(self.state[self.W1])
        # print(nr_waiting_patients)

        max_wait = max(nr_waiting_patients)
        mean_wait = mean(nr_waiting_patients)
        throughput = self.state[-1] / (self.t_max * 10 * mean_wait + 1)

        wait_counter = Counter(nr_waiting_patients)

        print("------- last simulation summary -------")
        print(f"Throughput: {throughput}" )
        print(f"mean number of people waiting: {mean_wait}")
        print(f"number of emergencies: {self.nr_emergencies}")
        print()

        return self.schedule, throughput, wait_counter, max_wait, mean_wait

    def run_multiple(self, nr_runs):

        sum_counter = [0 for i in range(2*self.t_max)]
        sum2_counter = [0 for i in range(2*self.t_max)]
        mean_wait_times = deque()
        halfwidth_wait_times = deque()
        avarage_wait_times = deque()
        max_wait_time = 0
        for _ in range(nr_runs):
            schedule, throughput, wait_counter, max_wait, mean_wait = self.run()
            for c in wait_counter.items():
                sum_counter[c[0]] += c[1]
                sum2_counter[c[0]] += c[1]**2
            if max_wait > max_wait_time:
                max_wait_time = max_wait
            avarage_wait_times.append(mean_wait)
        print(sum_counter)
        print(sum2_counter)

        # CI for mean value
        mean_total = mean(avarage_wait_times)
        std_total = std(avarage_wait_times)
        halfwidth = 1.96*std_total/sqrt(nr_runs)
        ci_mean = (mean_total-halfwidth, mean_total+halfwidth)

        # determining mean and variances of each value of W
        for i in range(max_wait_time+1):
            mean_x = sum_counter[i] / (self.t_max*nr_runs)
            var_x = sum2_counter[i] / (self.t_max*nr_runs) - mean_x**2
            halfwidth_x = 1.96*sqrt(var_x / nr_runs)
            mean_wait_times.append(mean_x)
            halfwidth_wait_times.append(halfwidth_x)

        return array(mean_wait_times), array(halfwidth_wait_times), ci_mean


def plot_results(nr_runs):
    schedule = 75*[0]+25*[2]
    model = BasicModel(0.5, 0, schedule=schedule)
    means, halfwidth, average = model.run_multiple(nr_runs)
    plt.figure()
    labels = arange(len(means))
    plt.bar(labels, means, width=0.5, yerr=halfwidth)
    plt.show()


def plot_multiple(nr_runs):
    schedule1 = [2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 2, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 1, 1, 0, 0, 2, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1]
    schedule2 = 50*[1,0]
    model1 = BasicModel(0.5, 0.02)
    model2 = BasicModel(0.5, 0.02, 5)
    model3 = BasicModel(0.5, 0.02, 10)
    y1, dy1, E_y1 = model1.run_multiple(nr_runs)
    y2, dy2, E_y2 = model2.run_multiple(nr_runs)
    y3, dy3, E_y3 = model3.run_multiple(nr_runs)
    print(E_y1)
    print(E_y2)
    print(E_y3)
    fig, ax = plt.subplots(figsize=(12, 6))
    length = min([len(y1), len(y2), len(y3), 15])
    labels = arange(length)
    w = 0.3
    ax.bar(labels - w, y1[:length], width=w, yerr=dy1[:length], label='basic')
    ax.bar(labels, y2[:length], width=w, yerr=dy2[:length], label='with emergencies')
    ax.bar(labels + w, y3[:length], width=w, yerr=dy3[:length], label='with doctor to late')
    plt.xlabel("Number of patients in W")
    plt.ylabel("Probability")
    plt.title("Distribution of number of patient in the waiting room")
    plt.legend()
    plt.show()


plot_multiple(10000)

if __name__ == "__main__":
    # manySimulations(numberOfSimulations=1000)
    print()