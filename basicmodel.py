from collections import deque
from random import random, seed
from numpy import mean
import matplotlib.pyplot as plt

# seed(10)

# A0,A1,A2,A3,A4,A5,W1,O0,O1, ... ,O10, O11, H

class BasicModel:
    def __init__(self, 
                prob_to_doc = 0.5,
                schedule : list = []):
        self.state = [0 for i in range(0,22)]
        self.time = 0
        self.schedule = schedule
        self.W1 = 6
        self.NOPTS = 2 # number of optomologists

        #Visitor probabilities 
        self.prob_1 = 0.5  #probability that 1 person enters building , 0.5
        self.prob_2 = 0.2  #probability that 2 people enters building , 0.2
        self.prob_3 = 0.1
        
        #self.prob_emergency = 0.02 #1/50
        self.prob_emergency = 0.04 #1/25

        self.prob_to_doc = prob_to_doc # the probability that somebody has to go to the doctor after visiting one of the assistents

        self.prob_skipsA2 = 1
        self.prob_skipsA4 = 0.5
        self.prob_skipsO2n = 0.5

        # Emergency state
        self.EMERGENCY = False
        self.nr_emergencies = 0
        # Initialise the removed persons list
        self.removedPersonIndices = []
    
    def reset_state(self):
        self.state = [0 for i in range(0,22)]
    
    def reset_schedule(self):
        self.schedule = []

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
        if len(self.schedule) == self.t_max:
            self.state[0] += self.schedule[self.time]
            return


        r = random()
        if 0 < r <= self.prob_1:
            # Add one person 
            peopleToAdd = 1

            self.state[0] = self.state[0] + peopleToAdd
            self.schedule.append(peopleToAdd)
        elif self.prob_1 < r <= self.prob_1 + self.prob_2:
            peopleToAdd = 2

            self.state[0] = self.state[0] + peopleToAdd
            self.schedule.append(peopleToAdd)
        # elif self.prob_1 + self.prob_2 < r <= self.prob_1 + self.prob_2 + self.prob_3:
        #     peopleToAdd = 3
        #     self.state[0] =  self.state[0] + peopleToAdd
        #     self.schedule.append(peopleToAdd)
        # elif self.prob_1 + self.prob_2 + self.prob_3 < r <= self.prob_1 + self.prob_2 + self.prob_3 + self.prob_4:
        #     peopleToAdd = 4
        #     self.state[0] =  self.state[0] + peopleToAdd
        #     self.schedule.append(peopleToAdd)
        else:
            self.schedule.append(0)

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
            #print("emergency")
            self.state[self.W1] += 1
            self.nr_emergencies += 1


    def round(self):
        """
        5 minutes pass
        """
        
        #self.check_emergency()
        self.state = self.moveOPeople(self.state)
        self.state = self.moveAPeople(self.state)
        self.visitor()
        self.time += 1
        #print(self.state)

    def run(self, t_max):
        """
        Run one simulation
        """
        #Reset variables for next run
        self.reset_state()
        self.nr_emergencies = 0
        self.t_max = t_max

        if (len(self.schedule) != t_max) and (len(self.schedule) != 0):
            print("Schedule does not match number of timesteps for this simulation.")
            self.reset_schedule()

        nr_waiting_patients = deque()
        for t in range(t_max):
            self.round()
            nr_waiting_patients.append(self.state[6])
        # print(nr_waiting_patients)

        numberOfPeopleInWaitingRoomMean = mean(nr_waiting_patients)
        throughput = self.state[-1] / (t_max * 10 * numberOfPeopleInWaitingRoomMean + 1)

        #print("------- last simulation summary -------")
        #print(f"Throughput: {throughput}" )
        #print(f"mean number of people waiting: {numberOfPeopleInWaitingRoomMean}")
        #print(f"number of emergencies: {self.nr_emergencies}")
        #print()

        result = self.schedule, throughput
        self.reset_schedule()

        return(result)


def manySimulations(numberOfSimulations: int):
    BM = BasicModel()

    # Initialise variables that return the best result
    max_throughput = 0
    best_schedule = []

    for _ in range(numberOfSimulations):
        schedule, throughput =  BM.run(50)
        if throughput > max_throughput:
            best_schedule = schedule
            max_throughput = throughput
    print("\n--------------- Result -----------------")
    print(f"The best found schedule is {best_schedule}")
    print(f"Gave highest throughput: {max_throughput}")


def plotThroughput(numberOfSimulations: int = 1000):
    BM = BasicModel()

    # Set the figure size in inches
    plt.figure(figsize=(10,6))

    x = []
    y = []
    
    for i in range(numberOfSimulations):
        schedule, throughput =  BM.run(50)
        x.append(i)
        y.append(throughput)
    
    plt.scatter(x, y, label = "(i,throughput)")

    # Set x and y axes labels
    plt.xlabel('i (i-th simulation)')
    plt.ylabel('Throughput for simulation i')

    plt.title('Throughput shown for all simulations')
    plt.legend()
    plt.show()

def plotOptimalThroughput(numberOfSimulations: int = 1000):
    BM = BasicModel()

    # Set the figure size in inches
    plt.figure(figsize=(10,6))

    x = []
    y = []
    best_schedule, best_throughput = [], 0
    
    for i in range(numberOfSimulations):
        schedule, throughput =  BM.run(50)
        if throughput > best_throughput:
            best_schedule = schedule
            best_throughput = throughput
        x.append(i)
        y.append(best_throughput)
    
    print("\n--------------- Result -----------------")
    print(f"The best found schedule is {best_schedule}")
    print(f"Gave highest throughput: {best_throughput}")

    plt.plot(x,y)
    # Set x and y axes labels
    plt.xlabel('i-t simulation')
    plt.ylabel('Best throughput found')

    plt.title('Best throughputs')
    plt.legend()
    plt.show()

def exampleWithGivenSchedule():
    schedule = schedule = [1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 2, 1, 0, 0, 0, 0, 0, 0, 1, 2, 0, 1, 1, 0, 0, 0, 2, 0, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 2, 0, 0, 1, 0, 0, 0, 0, 2, 0, 0, 1, 0, 0, 1, 2, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0]
    BM = BasicModel(schedule = schedule)
    schedule, throughput = BM.run(t_max= 50)
    print("\n--------------- Result -----------------")
    print(f"Schedule: {schedule}")
    print(f"Throughput: {throughput}")
    

if __name__ == "__main__":
    #manySimulations(numberOfSimulations=10000)
    
    #plotThroughput(1000)

    # note that this gives a plot with different simulations than the one from above
    plotOptimalThroughput(10000)

    #exampleWithGivenSchedule()
