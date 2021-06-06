
from collections import deque, Counter
from math import sqrt
from random import random, seed
from numpy import mean, arange, array, std
from matplotlib import pyplot as plt
from scipy import stats

# seed(10)

# A0,A1,A2,A3,A4,A5,W1,O0,O1, ... ,O10, O11, H



class BasicModel:
    def __init__(self, prob_to_doc=0.5, prob_emergency=0.02, mean_doc_arr_time=1, schedule=[]):
        self.state = [0 for i in range(0, 22)]
        self.schedule = schedule
        self.t_max = 100
        self.time = 0
        self.W1 = 6
        self.NOPTS = 2 # number of optomologists
        self.distribution = stats.geom(1/mean_doc_arr_time)

        #Visitor probabilities 
        self.prob_1 = 0.3  #probability that 1 person enters building
        self.prob_2 = 0.1  #probability that 2 people enters building
        self.prob_emergency = prob_emergency #1/50
        self.prob_to_doc = prob_to_doc # the probability that somebody has to go to the doctor after visiting one of the assistents

        self.prob_skipsA2 = 0.5
        self.prob_skipsA4 = 0.5
        self.prob_skipsO2n = 0.5

        # Emergency state
        self.EMERGENCY = False
        self.nr_emergencies = 0
        # Initialise the removed persons list
        self.removedPersonIndices = []
    
    def reset_state(self):
        self.state = [0 for i in range(0, 22)]

    def peopleAtOphthalmologist(self):
            return sum(self.state[self.W1 + 1 : -1])
    
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
        busyOpts = sum(li[7:-2])
        freeOpts = self.NOPTS - busyOpts

        li[21] += li[20]
        li[20] = 0
        li = self.skipO2n(li, 19)

        li[19] = li[18]
        li[18] = 0
        li = self.skipO2n(li, 17)

        li[17] = li[16]
        li[16] = 0
        li = self.skipO2n(li, 15)

        li[15] = li[14]
        li[14] = 0
        li = self.skipO2n(li, 13)

        li[13] = li[12]
        li[12] = 0
        li = self.skipO2n(li, 11)

        li[11] = li[10]
        li[10] = 0
        li = self.skipO2n(li, 9)

        li[9] = li[8]
        li[8] = 0
        li = self.skipO2n(li, 7)
        li[7] = 0


        # # Add the number of free optomologists to O1
        toAdd = min(freeOpts, li[6])
        li[7] += toAdd
        li[6] -= toAdd

        return li


    def moveAPeople(self, li: list):
        """
        Determines what happens to people who are at one of the assistants.
        
        We assume that the waiting room and the optomologists have already been handled.
        The queue starts moving at the front (aka A5 moves first)
        """

        # A5 moves to W1 or H
        for _ in range(li[5]):
            to_doc = random() < self.prob_to_doc
            if to_doc:
                li[6] += 1
            else:
                li[-1] += 1 # here they go home already

        # A3 or A4 moves to A5
        li[5] = li[4]
        li[4] = 0
        for _ in range(li[3]):
            skipA4 = random() < self.prob_skipsA4
            if skipA4:
                li[5] += 1
            else:
                li[4] += 1
        
        # A1 or A2 moves to A3
        li[3] = li[2]
        li[2] = 0
        for _ in range(li[1]):
            skipA2 = random() < self.prob_skipsA2
            if skipA2:
                li[3] += 1
            else:
                li[2] += 1
        
        # A0 moves to A1
        li[1] = li[0]

        # A0 = 0
        li[0] = 0

        return li

    def visitor(self):
        if len(self.schedule)>0 and self.time <= self.t_max:
            peopleToAdd = self.schedule[self.time]
        else:
            r = random()
            if 0 < r <= self.prob_1:
                # Add one person
                peopleToAdd = 1

            elif self.prob_1 < r <= self.prob_1 + self.prob_2:
                peopleToAdd = 2
            else:
                peopleToAdd = 0
        self.state[0] = self.state[0] + peopleToAdd


    def addEmergency(self):
        """
        What happens during emergency:
        1. Emergency comes into clinic and is immediately placed with an ophthalmologist
        2. This means one person now has to wait for the ophthalmologist to return from the emergency case
        3. We will remove that person from the ophthalmologist and put him in the waiting room.
        4. When the emergency is over, we put him back where he/she originally was.

        What happened before this function was called:
        1. A probability was computed and with 0.02 probability an emergency occurs. In that case, this function is called.
        """

        # Are there any free ophthalmologists
        if self.peopleAtOphthalmologist() <= self.NOPTS -1:
            pass
        else: # there are no free ophthalmologists
            # Detect where person in front is
            i = -2
            while True :
                if self.state[i] != 0:
                    removedPersonIndex = i
                    self.removedPersonIndices.append(removedPersonIndex)
                    break
                i -= 1
        
            # remove person from ophthalmologist
            self.state[removedPersonIndex] -= 1
            # add removed person to waiting room
            self.state[self.W1] += 1
            self.EMERGENCY = True
        
        # add emergency to O1
        self.state[self.W1 + 1] += 1
        

    def handleEmergency(self):
        """
        This function together with 'addEmergency' handle everything related to emergencies
        """
        if self.EMERGENCY and self.peopleAtOphthalmologist() <=self.NOPTS -1 : # this means that the emergency possibly just finished, since there is a free spot now
            removedPersonIndex = self.removedPersonIndices.pop(0)
            self.state[removedPersonIndex] += 1

            # If the removed people list is empty, then apparently there is no more emergency, so set emergency attribute to false
            if not self.removedPersonIndices:
                self.EMERGENCY = False
        elif self.EMERGENCY and self.peopleAtOphthalmologist() == 2: # There is still an unfinished emergency case
            pass
        

        # Possibly generate a new emergency with probability self.prob_emergency
        if random() <= self.prob_emergency:
            self.addEmergency()
            print("\nemergency!")
            print(self.state)
            print(f"REMOVED PEOPLE: {self.removedPersonIndices}\n")


    def check_emergency(self):

        if random() <= self.prob_emergency:
            print("emergency")
            self.state[self.W1] += 1
            self.nr_emergencies += 1


    def round(self):
        """
        5 minutes pass
        """
        
        self.check_emergency()
        self.state = self.moveOPeople(self.state)
        self.state = self.moveAPeople(self.state)
        self.visitor()
        #print(self.state)

    def run(self, t_max):
        """
        Run one simulation
        """
        # Reset variables for next run
        self.reset_state()
        self.nr_emergencies = 0
        self.NOPTS = 1
        nr_waiting_patients = deque()
        arr_time = self.distribution.rvs()

        for t in range(t_max):
            self.time = t
            if t == arr_time:
                self.NOPTS += 1
            self.round()
            nr_waiting_patients.append(self.state[6])
        # print(nr_waiting_patients)

        max_wait = max(nr_waiting_patients)
        mean_wait = mean(nr_waiting_patients)
        throughput = self.state[-1] / (t_max * 5 * mean_wait + 1)

        wait_counter = Counter(nr_waiting_patients)

        print("------- last simulation summary -------")
        print(f"Throughput: {throughput}" )
        print(f"mean number of people waiting: {mean_wait}")
        print(f"number of emergencies: {self.nr_emergencies}")
        print()

        return (self.schedule, throughput, wait_counter, max_wait, mean_wait)

    def run_multiple(self,t_max, nr_runs):

        sum_counter = [0 for i in range(2*t_max)]
        sum2_counter = [0 for i in range(2*t_max)]
        mean_wait_times = deque()
        halfwidth_wait_times = deque()
        avarage_wait_times = deque()
        max_wait_time = 0
        for _ in range(nr_runs):
            schedule, throughput, wait_counter, max_wait, mean_wait = self.run(t_max)
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
            mean_x = sum_counter[i] / (t_max*nr_runs)
            var_x = sum2_counter[i] / (t_max*nr_runs) - mean_x**2
            halfwidth_x = 1.96*sqrt(var_x / nr_runs)
            mean_wait_times.append(mean_x)
            halfwidth_wait_times.append(halfwidth_x)

        return array(mean_wait_times), array(halfwidth_wait_times), ci_mean

def manySimulations(numberOfSimulations: int):
    BM = BasicModel()

    # Initialise variables that return the best result
    max_throughput = 0
    best_schedule = []

    for _ in range(numberOfSimulations):
        schedule, throughput, wait =  BM.run(100)
        if throughput > max_throughput:
            best_schedule = schedule
            max_throughput = throughput
    print("\n--------------- Result -----------------")
    print(f"The best found schedule is {best_schedule}")
    print(f"Gave highest throughput: {max_throughput}")


def plot_results(t_max, nr_runs):
    schedule = 75*[0]+25*[2]
    model = BasicModel(0.5, 0, schedule=schedule)
    means, halfwidth, average = model.run_multiple(t_max, nr_runs)
    plt.figure()
    labels = arange(len(means))
    plt.bar(labels, means, width=0.5, yerr=halfwidth)
    plt.show()


def plot_multiple(t_max, nr_runs):
    schedule1 = [2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 2, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 1, 1, 0, 0, 2, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1]
    schedule2 = 50*[1,0]
    model1 = BasicModel(0.5, 0.02)
    model2 = BasicModel(0.5, 0.02, 5)
    model3 = BasicModel(0.5, 0.02, 10)
    y1, dy1, E_y1 = model1.run_multiple(t_max, nr_runs)
    y2, dy2, E_y2 = model2.run_multiple(t_max, nr_runs)
    y3, dy3, E_y3 = model3.run_multiple(t_max, nr_runs)
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



plot_multiple(100, 10000)
# model = BasicModel(0.5)
# y, dy = model.run_multiple(100, 10000)
# plot_results(y,dy)

if __name__ == "__main__":
    # manySimulations(numberOfSimulations=1000)
    print()