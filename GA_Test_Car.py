import pyglet
from classes.geneticAlgoritm.world import World
from classes.circuit import circuit
from classes.Vector import Vector2D

### MAIN LOOP
window = pyglet.window.Window(resizable=True, fullscreen=True)

inner_points = [[18,3],[8,3],[5,4],[3,6],[2,9],[2,12],[3,14],[4,14],[6,12],[7,8],[8,7],[12,6],[16,6],[19,9],[20,11],[16,13],[13,12],[12,14],[13,15],[17,16],[20,15],[22,13],[23,8],[21,5]]
outer_points = [[18,0],[8,0],[2,3],[0,9],[0,14],[2,16],[5,16],[8,12],[9,9],[12,8],[15,8],[17,10],[16,11],[12,10],[11,11],[10,13],[10,15],[12,17],[17,17],[20,16],[23,14],[25,8],[23,4]]
inner = [Vector2D(i[0],i[1]) for i in inner_points]
outer = [Vector2D(i[0],i[1]) for i in outer_points]

checkpoints = [[[10,-1],[10,4]],[[4,1],[6,4]],[[0,6],[3,7]],[[-1,13],[3,12]],[[4,13],[7,15]],[[6,9],[10,11]],[[11,5],[12,9]],[[15,10],[18,7]],[[15,10],[14,13]],[[9,14],[13,13]],[[15,17],[16,15]],[[21,12],[24,15]],[[22,8],[25,6]],[[19,5],[20,1]],[[15,-1],[15,4]]]
circuit_checkpoints = []
for i, checkpoint in enumerate(checkpoints):
    circuit_checkpoints.append([])
    for x, point in enumerate(checkpoint):
        circuit_checkpoints[i].append(Vector2D(point[0],point[1]))

circ = circuit.fromFullPoints([inner, outer], circuit_checkpoints, Vector2D(12,1))
world = World(50, circ.startingPoint.x, circ.startingPoint.y, window=window.get_size())
batch = pyglet.graphics.Batch()

running = True

key = pyglet.window.key
key_handler = key.KeyStateHandler()

@window.event
def on_close():
    running = False

@window.event
def on_draw():
    render()

def update(dt):
    window.push_handlers(key_handler)
    if(world.allCarsDead()):
        world.calcFitness()
        world.naturalSelection()
        world.mutateAll()
    else:
        if key_handler[key.S]:
            world.show = True
        if key_handler[key.H]:
            world.show = False
        if key_handler[key.B]:
            world.showA = False
            print(world.bestCar)
        if key_handler[key.A]:
            world.showA = True

        carList = world.carList
        for car in carList:
            hitbox = world.generateHitbox(car)
            # circ.carCollidedWithCheckpoint(hitbox)
            if circ.collidedWithCar(hitbox) == True:
                car.dead = True
        
        world.update(dt)

def render():
    window.clear()

    foreground = pyglet.graphics.OrderedGroup(2)
    background = pyglet.graphics.OrderedGroup(1)
    circuitLayer = pyglet.graphics.OrderedGroup(0)

    carDrawings = world.draw(batch, foreground, background, circ.vertices)
    circuitDraw = circ.draw(batch, window.get_size(), circuitLayer)
    goal = pyglet.shapes.Circle(window.get_size()[0]-10, window.get_size()[1]-10, 10, color=(0,255,0), batch=batch)
    batch.draw()

if __name__ == "__main__":
    pyglet.clock.schedule_interval(update, 1/120.0)
    pyglet.app.run()