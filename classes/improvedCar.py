from typing import List
import pyglet
import math
from classes.improvedLine import linline
from classes.Vector import Vector2D

class Car():
    def __init__(self, mass):
        self.mass = 1
        self.forces = Vector2D(0,0)
        self.acceleration = Vector2D(0,0)
        self.velocity = Vector2D(0,0)
        self.startPosition = Vector2D(x, y)
        self.position = Vector2D(x, y)

        self.sprites = {"alive": pyglet.resource.image('img/car.png'),"best": pyglet.resource.image('img/carBest.png'),"dead": pyglet.resource.image('img/carCrash.png')}
        self.scale = 1.48
        self.image_dimensions = (self.sprites['alive'].width, self.sprites['alive'].height)

        self.carRotation = Vector2D(1,1)

        self.eyesList = [[0, 5000], [5000, 5000], [5000, 0], [5000, -5000], [0, -5000], [-5000, 0]]
        self.hitboxVectors = [
            Vector2D(-self.image_dimensions[0]/2,-self.image_dimensions[1]/2),
            Vector2D(-self.image_dimensions[0]/2,self.image_dimensions[1]/2),
            Vector2D(self.image_dimensions[0]/2,self.image_dimensions[1]/2),
            Vector2D(self.image_dimensions[0]/2,-self.image_dimensions[1]/2),
        ]

        self.dead = False
        self.middle = Vector2D(self.image_dimensions[0]//2,self.image_dimensions[1]//2)
        
        self.lines = []
        
        self.currentCheckpoint = 0

        #GA
        self.bestCar = False
        self.fitness = 0
        self.currentLap = 0

    def draw(self, batch, group, best=False):
        car = self.drawCar(batch, group, best)
        return car


    def draw2(self, batch, layers, options="f"):
        
        drawList = [self.drawCar(batch, layers['car']),
            self.eyes(batch, layers['background']),
            self.hitbox(batch, layers['background']),
        ]

        return drawList


    def drawCar(self, batch, group, best=False):
        if self.dead:
            car = pyglet.sprite.Sprite(self.sprites['dead'], x=self.position.x, y=self.position.y, batch=batch, group=group)
            car.opacity = 25
        elif best:
            car = pyglet.sprite.Sprite(self.sprites['best'], x=self.position.x, y=self.position.y, batch=batch, group=group)    
            car.opacity = 100
        else:
            car = pyglet.sprite.Sprite(self.sprites['alive'], x=self.position.x, y=self.position.y, batch=batch, group=group)
            car.opacity = 75
        
        #### NOOOO I WANT TO SEE MY FREAKING CAR 
        car.opacity = 100

        car.scale = self.scale
        car.anchor_x = car.width / 2
        car.anchor_y = car.height / 2
        car.rotation = -(self.carRotation.rotation())
        return car

    def eyes(self, batch, group):
        eyes = self.drawEyes(batch, group)
        return eyes

    def drawEyes(self, batch, group):
        lines = self.generateLines()
        out = []

        for line in lines:
            out.append(line.draw(batch, group, [1920, 1080], 5))
        return out

    def generateLines(self):
        lines = []
        eyePoints = [Vector2D(i[0],i[1]) for i in self.eyesList]

        for line in eyePoints:
            secondPosition = self.middle + line.rotate(self.carRotation.rotation())
            lines.append(linline.fromPoints(self.middle, secondPosition))

        self.lines = lines
        return lines

    def hitbox(self, batch, group):
        out = []
        hitboxVectors = self.generateHitbox()

        for hitboxLine in hitboxVectors:
            out.append(hitboxLine.draw(batch, group))
        return out

    def generateHitbox(self):
        hitbox = []
        lineColor = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255)]

        rotation = self.carRotation.rotation()

        points = [point.rotate(rotation, in_place=False) + self.middle for point in self.hitboxVectors]
        for i in range(len(points)):
            l = linline.fromPoints(points[i-1], points[i])
            l.color = lineColor[i]
            hitbox.append(l)

        return hitbox

    def observe(self):
        observations = [abs(self.velocity), abs(self.acceleration)]
        
        for point in self.circuitIntersections:
            observations.append(abs(self.middle - point))
        
        return observations
        
    def intersectEyes(self, batch, lines, group):
        dots = []
        self.circuitIntersections = []

        for n, eyeline in enumerate(self.lines):
            intersect = [w for l in lines if (w:=l.intersect(eyeline)) != None]
            minList = [abs(self.middle - point) for point in intersect]
            if len(minList):
                pointIndex = [i for i, j in enumerate(minList) if j == min(minList)]
                point = intersect[pointIndex[0]]
                self.circuitIntersections.append(point)
                dots.append(pyglet.shapes.Circle(point.x, point.y, 5, color=(255,0,0), batch=batch, group=group))
                #dots.append(pyglet.shapes.Circle(point.x, point.y, 5, color=(255,0,0), batch=batch, group=group))
        return dots

    def mathIntersect(self, lines):
        self.circuitIntersections = []
        for eyeline in self.generateLines():
            intersect = [l.intersect(eyeline) for l in lines if l.intersect(eyeline) != None]
            minList = [abs(self.middle - point) for point in intersect]
            if len(minList):
                pointIndex = [i for i, j in enumerate(minList) if j == min(minList)]
                self.circuitIntersections.append(intersect[pointIndex[0]])
            else:
                for l in lines:
                    print(l.intersect(eyeline, debug=True))
                print(self.position)
                print(self.velocity)
                print(self.carRotation.rotation())
                print(self.acceleration)



    def forward(self):
        self.forces += Vector2D(100,0)

    def backward(self):
        self.forces += Vector2D(-100,0)

    def left(self):
        self.forces += Vector2D(0, self._getTurnForce())

    def right(self):
        self.forces += Vector2D(0,-self._getTurnForce())

    def update(self, dt, key, key_handler):
        self.forces = Vector2D(0,0)

        if key_handler[key.UP]:
            self.forward()
        if key_handler[key.DOWN]:
            self.backward()
        if key_handler[key.LEFT]:
            self.left()
        if key_handler[key.RIGHT]:
            self.right()
        
        self._calculatePhysics(dt)

    def updateWithInstruction(self, dt, instruction):
        self.forces = Vector2D(0,0)

        if(instruction == 0):
            self.forward()
        elif(instruction == 1):
            self.backward()
        elif(instruction == 2):
            self.left()
        elif(instruction == 3):
            self.right()
        elif None:
            pass
        else:
            print("Notice: UpdateWithInstruction() can only handle ints from 0 to 3")
        
        self._calculatePhysics(dt)


    def _getTurnForce(self):
        return 4000

    def _calculatePhysics(self, dt):
        #Calculate acceleration based on forces and limit it to 100 pixels per second per second
        self.acceleration = self.forces.rotate(self.carRotation.rotation()) / self.mass
        self.acceleration.limit(200)

        #Calculate velocity based on accelation and limit it to 200 pixels per second
        self.velocity += self.acceleration * dt
        self.velocity.limit(200)
        
        #Determine if we are driving backwards or forwards
        backwards = (self.velocity @ self.carRotation < 0)

        self.position += self.velocity * dt
        if not backwards:
            self.carRotation = self.velocity.copy()
        else:
            self.carRotation = -self.velocity.copy()
        
        self.middle = self.position + Vector2D.fromTuple(self.image_dimensions).rotate(self.carRotation.rotation()) * self.scale * 0.5
        
    def reset(self):
        self.forces = Vector2D(0,0)
        self.acceleration = Vector2D(0,0)
        self.velocity = Vector2D(0,0)
        self.position = self.startPosition.copy()