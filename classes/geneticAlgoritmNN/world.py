import random
import pandas as pd
from random import sample
from classes.Vector import Vector2D
from classes.geneticAlgoritmNN.agent import Agent
from pyglet import shapes
from openpyxl import load_workbook

class World:
    def __init__(self, cars, circ, window, load=False, car_scale=1.48) -> None:
        self.window = Vector2D.fromTuple(window)
        self.circuit = circ
        self.carX = self.circuit.startingPoint.x
        self.carY = self.circuit.startingPoint.y
        self.carList = [Agent(self.carX, self.carY, window=self.window, scale=car_scale) for _ in range(cars)]
        self.oldCarList = []
        self.show = False
        self.showA = True
        self.carCount = cars

        self.fitnessSum = 0
        self.gen = 1
        self.autoGen = 1

        self.bestCar = 0
        self.oldBestAgent = self.carList[self.bestCar]
        self.bestCarPosition = Vector2D(0,0)
        self.oldBestCount = 0

        self.maxStep = 1000
        self.load = load
        self.row = None
        self.blindSpots = []
        self.blindIndex = []
        self.addBlindSpot()

    def draw(self, batch, foreground, background, vertices):
        if self.showA:
            drawList = [car.draw(batch, foreground, background, vertices, self.show) for car in self.carList]
        else:
            car = self.carList[0]
            drawList = car.draw(batch, foreground, background, vertices, self.show)
        return drawList
    
    def drawBestCarPlace(self, batch, bestCarPlace):
        drawPlace = shapes.Circle(self.bestCarPosition.x,self.bestCarPosition.y,20,color=(0,255,0),batch=batch,group=bestCarPlace)
        drawPlace.opacity = 150
        return drawPlace

    def addBlindSpot(self):
        for line in self.circuit.skeletonLines:
            startPoint, _ = line.getEndPoints()
            self.blindSpots.append(startPoint)
        for i in range(len(self.blindSpots)):
            self.blindIndex.append(i)

    def drawBlindSpot(self, batch, group):
        out = []
        for point in self.blindSpots:
            shape = shapes.Circle(point.x,point.y,10,color=(255,20,20),batch=batch,group=group)
            out.append(shape)
        return out

    def update(self, dt):
        for agent in self.carList:
            if agent.step > self.maxStep:
                agent.dead = True
            else:
                hitbox = self.generateHitbox(agent)
                agent.car.currentCheckpoint = self.circuit.carCollidedWithCheckpoint(agent.car)
                if self.circuit.collidedWithCar(hitbox) == True:
                    agent.dead = True

                agent.update(dt, self.circuit.vertices)

    def generateHitbox(self, agent):
        hitbox = agent.generateHitbox()
        return hitbox
        
    def allCarsDead(self) -> bool:
        for car in self.carList:
            if not car.dead:
                return False
        return True

    def calcFitness(self):
        for car in self.carList:
            car.calcFitness(self.circuit.skeletonLines, self.circuit.checkpointNumber, self.blindSpots, self.blindIndex)

    def naturalSelection(self):
        self.gen += 1
        self.autoGen += 1
        if self.autoGen == 10:
            self.autoGen = 0
            self.carList[0].nn.autoSaveWeights()
        print("------------------------------------------------------------------------------------------------------------------------------")
        print(f"NEXT GEN: {self.gen}")

        check = []
        check2 = []
        check3= []
        for agent in self.carList:
            check.append(agent.car.currentCheckpoint)
            check2.append(agent.fitness)
            check3.append(agent.index)

        if self.row == None:
            self.row = 0
        else:
            self.row += 51

        dict = {'Checkpoint': check, 'Fitness': check2, 'Index': check3}
        excelList = pd.DataFrame(dict)

        #excelList.to_excel(r'C:\Users\Tboefijn\OneDrive\Documenten\dataPrintPws.xlsx', index = False, startrow = self.row, header = True)

        ### Bij data opslaan deze aanzetten ###
        #excelList.to_csv(r'C:\Users\Tboefijn\OneDrive\Documenten\dataPrintPws.csv', mode='a', header=True)
        print(excelList)

        nextGen = []
        self.setBestCar()
        self.calcFitnessSum()

        nextGen.append(self.carList[self.bestCar].clone(self.carX, self.carY, best=True))
        for _ in range(1, len(self.carList)):
            parent = self.selectParent()
            if parent != None:
                nextGen.append(parent.clone(self.carX, self.carY, best=False))
            else:
                nextGen.append(Agent(self.carX,self.carY,window=self.window,best=False))
            
        self.carList.clear()
        self.carList = nextGen[:]
        del nextGen

    def mutateAll(self):
        print(self.oldBestCount)
        if self.oldBestCount % 5 == 0 and self.oldBestCount != 0:
            for i in range(1, len(self.carList)):
                self.carList[i].nn.mutationRate += 0.1
                self.carList[i].nn.mutate()
            print("Count +")
        elif (self.oldBestCount == 0):
            print("Rate reset")
            for i in range(1, len(self.carList)):
                self.carList[i].nn.mutationRate = 0.25
                self.carList[i].nn.mutate()
        else:
            print("Something something")
            for i in range(1, len(self.carList)):
                self.carList[i].nn.mutate()

    def crossParenting(self, x):
        if len(self.carList) > 10:
            selectList = []
            selectList = self.carList[1:]
            for i in range(x):
                newCar = Agent(self.carX,self.carY,window=self.window,best=False)
                randomCars = sample(selectList, 2)
                newCar.nn = randomCars[0].nn.crossParent(randomCars[1].nn)
                if randomCars[0] in self.carList and randomCars[1] in self.carList:
                    if randomCars[0] == randomCars[1]:
                        self.carList.remove(randomCars[0])
                    else:
                        self.carList.remove(randomCars[0])
                        self.carList.remove(randomCars[1])
                self.carList.append(newCar)

        while len(self.carList) != self.carCount:
            self.carList.append(Agent(self.carX,self.carY,window=self.window,best=False))

    def selectParent(self):
        rand = random.random() * self.fitnessSum
        runningSum = 0

        for agent in self.carList:
            runningSum += agent.fitness
            if runningSum > rand:
                return agent
        return None

    def calcFitnessSum(self):
        fitnessSum = 0
        for car in self.carList:
            fitnessSum += car.fitness
        self.fitnessSum = fitnessSum

    def setBestCar(self):
        topFitness = 0
        
        for i, car in enumerate(self.carList):
            if(car.fitness > topFitness):
                topFitness = car.fitness 
                self.bestCar = i
        
        if self.carList[self.bestCar].fitness > self.oldBestAgent.fitness or self.gen == 2:
            self.bestCarPosition = self.carList[self.bestCar].car.position
            self.oldBestAgent = self.carList[self.bestCar]
            self.oldCarList = self.carList[:]
            self.oldBestCount = 0
            print("Count reset")
            print(f"Best Car: {self.bestCar}")
        else:
            print("Old Best")
            print(f"Best Car: {self.bestCar}")

            self.carList = []
            self.carList = self.oldCarList[:]
            self.bestCar = self.carList.index(self.oldBestAgent)
            self.oldBestCount += 1
            print(f"Best Car: {self.bestCar}")
