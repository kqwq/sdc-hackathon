'''
========================== INTRODUCTION ==========================
Hello! Welcome to the monolith that is this code. Here is an overview
of the code and what each class does.

Around 85% of this code was typed by hand and 15% was generated with GitHub Copilot.
The 2D transformations and rotations were derived by hand, I have done this in the 
past with similar projects in both Python and JavaScript. I am fully capable of
writing and explaining each line of code without AI/Internet, AI was used to
speed up development in some cases, especially in parts like Turret.draw(self) and
EnemyMotherShip.updatePoints(self).

========================== CODE OVERVIEW ==========================
Abstract classes
- WorldObject: Parent class of all objects that exist in 2D space

WorldObject classes
- Shields: Protects mother ships from laser beams and regenerates over time
- Explosion: A SFX element that deletes itself after 0.5 seconds
- LaserBeam: A fast-moving beam of light that damages ships and shields
- Tile: AllianceShip modular 2x1 part
- AllianceShip: Modular crewed ship consisting of tiles and doors
- SmallEnemyShip: Enemy counterpart to AllianceShip, but more simple
- CollisionWall: Collision wall that pushes Birds away from it
- TurretStation: Control station that birds can interact with to control Turrets
- AllianceMotherShip: "Star Destroyer"-like ship that houses various rooms
- EnemyMotherShip: Enemy counterpart to AllianceMotherShip but simplier and octagon-shaped
- Bird: Shared player and NPC controller
- Decoration: Very simple static object that can be a tree, book, etc.
- RectRoom: Similar to Decoration, but a rectangular grayish room

Controller and miscellaneous classes
- StoryController: Keeps track of the game's plot and controls objects
- LevelEditor: Active during the "level editor" screen, shows right sidebar
- DebugCircle: Debugging object to test the limits of the game's renderer system
- MenuText: Displays... menu text!
- MenuOption: Displays the menu option, I mean what else?
- HUD - todo merge with StoryController
- GameManager: Manages the game state
- Renderer: Renders shapes and images to the screen

Global vars
- root
- gameManager
- renderer
- objs


'''


import tkinter as tk
import random
import time
import renderer
import math

# Constants
DOOR_THICKNESS = 0.04
DOOR_LENGTH = 0.4
DOOR_OPEN_AMOUNT = 0.8
DOOR_OPEN_RADIUS = 0.35
DEBUG_MODE = False


# Define various objects
objs = []
objsWithHP = []
walls = []
storyController = None


class WorldObject:
  def __init__(self, x, y):
    objs.append(self)
    self.x = x
    self.y = y

  def update(self, delta):
    raise NotImplementedError("Subclasses should implement this!")

  def draw(self):
    raise NotImplementedError("Subclasses should implement this!")

class Shields(WorldObject):
  def __init__(self, x, y, w=1, h=1, color='blue'):
    super().__init__(x, y)
    objsWithHP.append(self)
    self.x = x
    self.y = y
    self.w = w
    self.h = h
    self.color = color
    self.thickness = 0.2
    self.brightness = 255
    self.hp = self.hpMax = 100
    self.hpRegen = 8
    
  def hit(self):
    self.brightness = 255
    
  def update(self, delta):
    if gameManager.scene_name == 'game':
      if self.brightness > 0:
        self.brightness -= min(self.brightness, max(1, round(delta * 255 * 2)))
  
    if self.hp < self.hpMax:
      self.hp += self.hpRegen * delta
    
  def draw(self):
    col = f'rgb(0,0,{self.brightness})'
    renderer.world_ellipse_outlined(self.x, self.y, abs(self.w), abs(self.h), col, self.thickness)
    
    
  

class Explosion(WorldObject):
  def __init__(self, x, y):
    super().__init__(x, y)
    self.size = 0.1
    self.color = 'orange'
    self.lifespan = 0.5

  def update(self, delta):
    self.size += delta * 2
    self.lifespan -= delta
    if self.lifespan < 0:
      objs.remove(self)

  def draw(self):
    renderer.world_circle(self.x, self.y, self.size, self.color)

class LaserBeam(WorldObject):
  def __init__(self, x, y, theta, originObj=None):
    super().__init__(x, y)
    self.speed = 120
    self.vx = math.cos(theta) * self.speed
    self.vy = math.sin(theta) * self.speed
    self.length = 2
    self.x2 = x + math.cos(theta) * self.length
    self.y2 = y + math.sin(theta) * self.length
    self.size = 0.03
    self.color = 'limegreen'
    self.lifespan = 5.0
    self.originObj = originObj

  def update(self, delta):
    self.x += self.vx * delta
    self.y += self.vy * delta
    self.x2 += self.vx * delta
    self.y2 += self.vy * delta
    self.lifespan -= delta
    if self.lifespan < 0:
      objs.remove(self)
      return
      
    # Collision with ships
    for obj in objsWithHP:
      if obj != self.originObj and obj.isInside(self.x, self.y):
        math.dist((self.x, self.y), (obj.x, obj.y)) < obj.size:
        obj.hp -= 1
        objs.remove(self)
        Explosion(self.x, self.y)
        return

  def draw(self):

    renderer.world_line(self.x, self.y, self.x2,
                        self.y2, self.color, self.size)


class Tile(WorldObject):
  def __init__(self, parent, x, y, type="ap", doorPositions=[]):
    super().__init__(x, y)
    '''
    ap - all purpose
    engine - engine unit
    weapon - weapon unit
    control - control unit
    '''
    self.parent = parent
    self.ax = parent.x + x  # accumulated x position
    self.ay = parent.y + y  # accumulated y position
    self.type = type
    self.image = renderer.load_image(f'tile-{type}.png')
    self.attached = True
    self.hp = 10
    self.doors = []  # (x, y, is-vertical, closed-amount)
    for doorPos in doorPositions:
      self.addDoor(doorPos)
    self.nearPlayer = False

  '''
  position is one of 0=top-left, 1=top-right, 2=right, 3=bottom-right, 4=bottom-left, 5=left
  '''

  def addDoor(self, position):
    doorPosTable = [
      [0.5, DOOR_THICKNESS, 0.5 - DOOR_LENGTH, DOOR_THICKNESS,
       0.5 + DOOR_LENGTH, DOOR_THICKNESS, False, 1],  # top-left
      [1.5, DOOR_THICKNESS, 1.5 - DOOR_LENGTH, DOOR_THICKNESS,
       1.5 + DOOR_LENGTH, DOOR_THICKNESS, False, 1],  # top-right
      [2 - DOOR_THICKNESS, 0.5, 2 - DOOR_THICKNESS, 0.5 - DOOR_LENGTH,
       2 - DOOR_THICKNESS, 0.5 + DOOR_LENGTH, True, 1],   # right
      [1.5, 1 - DOOR_THICKNESS, 1.5 - DOOR_LENGTH, 1 - DOOR_THICKNESS,
       1.5 + DOOR_LENGTH, 1 - DOOR_THICKNESS, False, 1],  # bottom-right
      [0.5, 1 - DOOR_THICKNESS, 0.5 - DOOR_LENGTH, 1 - DOOR_THICKNESS,
       0.5 + DOOR_LENGTH, 1 - DOOR_THICKNESS, False, 1],  # bottom-left
      [DOOR_THICKNESS, 0.5, DOOR_THICKNESS, 0.5 - DOOR_LENGTH,
       DOOR_THICKNESS, 0.5 + DOOR_LENGTH, True, 1],   # left
    ]
    self.doors.append(doorPosTable[position])

  def update(self, delta):
    self.ax = self.parent.x + self.x * \
      self.parent.ctheta - self.y * self.parent.stheta
    self.ay = self.parent.y + self.y * \
        self.parent.ctheta + self.x * self.parent.stheta
    tx, ty = self.transform(0, 0)

    if isinstance(me, Bird) and me.nearestShip == self.parent:
      if abs(me.insideTileX - self.x - 1) < 1.5 and abs(me.insideTileY - self.y - 0.5) < 1:
        self.nearPlayer = True
        for door in self.doors:
          if math.dist((me.x, me.y), self.transform(door[0], door[1])) < DOOR_OPEN_RADIUS:
            me.isNearDoor = True
            door[7] += ((1 - DOOR_OPEN_AMOUNT) - door[7]) * 0.25
          else:
            door[7] += (1 - door[7]) * 0.75
      else:
        self.nearPlayer = False

  def transform(self, x, y):
    return (
      self.parent.x + (self.x + x) * self.parent.ctheta -
        (self.y + y) * self.parent.stheta,
      self.parent.y + (self.y + y) * self.parent.ctheta +
        (self.x + x) * self.parent.stheta
    )

  def draw(self):

    if self.type == 'engine' and self.parent.usingEngines:
      ex, ey = self.transform(2.5, 0.5)
      lx, ly = self.transform(2, 0.1)
      rx, ry = self.transform(2, 0.9)
      renderer.world_polygon(
        [(ex, ey), (lx, ly), (rx, ry)], 'red')

    # renderer.world_rect(self.x - 0.1, self.y - 0.1, 2 + 0.2, 1 + 0.2, 'green')
    # renderer.world_img(self.image, self.ax, self.ay, 2)
    renderer.world_img_rot(self.image, self.ax, self.ay, 2, self.parent.theta)
    col = '#98F5F9'
    if DEBUG_MODE:
      col = 'red' if self.nearPlayer else 'blue'
    for cx, cy, d1x, d1y, d2x, d2y, isVertical, step in self.doors:
      dox = 0
      doy = 0
      if isVertical:
        doy = DOOR_OPEN_AMOUNT / 2 * step
      else:
        dox = DOOR_OPEN_AMOUNT / 2 * step
      d1x1, d1y1 = self.transform(d1x, d1y)
      d1x2, d1y2 = self.transform(d1x + dox, d1y + doy)
      d2x1, d2y1 = self.transform(d2x, d2y)
      d2x2, d2y2 = self.transform(d2x - dox, d2y - doy)
      renderer.world_line(d1x1, d1y1, d1x2, d1y2, col, DOOR_THICKNESS)
      renderer.world_line(d2x1, d2y1, d2x2, d2y2, col, DOOR_THICKNESS)

    if DEBUG_MODE:
      renderer.world_circle(self.ax, self.ay, 0.1, col)


class AllianceShip(WorldObject):
  def __init__(self, x, y, name="Basic"):
    super().__init__(x, y)
    objsWithHP.append(self)
    self.name = name
    self.tiles = []
    self.fuel = 10000
    self.vx = 0
    self.vy = 0
    self.theta = 0
    self.stheta = 0
    self.ctheta = 1
    self.rotSpeed = 1
    self.chairX = 0.25
    self.chairY = 0.5
    self.speed = 0
    self.maxSpeed = 20
    self.acc = 5
    self.usingEngines = False
    self.cockpit = None
    self.shootCooldown = 0
    self.shootCooldownMax = 0.1
    self.maxCamHt = 1.0
    if self.name == "Basic":
      self.convertToBasicShip()
    self.hp = 20
    self.size = 3
    
  # On delete, remove all tiles and create explosions in their place
  def destroy(self):
    for tile in self.tiles:
      Explosion(tile.ax, tile.ay)
      objs.remove(tile)
    self.tiles = []

  def convertToBasicShip(self):
    for tile in self.tiles:
      objs.remove(tile)
    self.tiles = [
      Tile(self, 2, -2, 'weapon-r', [4]),
      Tile(self, 1, -1, 'ap', [1, 3, 4]),
      Tile(self, 3, -1, 'engine'),
      Tile(self, 0, 0, 'control', [1, 3]),
      Tile(self, 2, 0, 'ap', [0, 2]),
      Tile(self, 1, 1, 'ap', [0, 3]),
      Tile(self, 3, 1, 'engine'),
      Tile(self, 2, 2, 'weapon-l', [0]),
    ]

  def player_control(self, delta):
    delta = min(delta, 0.1)
    acc = min(0.5, delta * self.acc)
    if keys.get('w', False):
      self.speed += (self.maxSpeed - self.speed) * acc
      self.usingEngines = True
    elif keys.get('s', False):
      self.speed += (0 - self.speed) * acc
      self.usingEngines = False

    if keys.get('a', False):
      self.theta -= delta * self.rotSpeed
    if keys.get('d', False):
      self.theta += delta * self.rotSpeed

    if keys.get('Return', False):
      global me
      keys['Return'] = False
      me = self.cockpit
      self.cockpit = None

    # On mouse press, find all weapon tiles and fire them
    self.shootCooldown -= delta
    if self.shootCooldown < 0 and mouse['left']:
      self.shootCooldown = self.shootCooldownMax
      for tile in self.tiles:
        if tile.type == 'weapon-l' or tile.type == 'weapon-r':
          # Find the nearest ship and fire the weapon
          if isinstance(tile, Tile) and tile.parent:
            x, y = tile.transform(1, 0.5)
            theta = self.theta + math.pi
            LaserBeam(x, y, theta, self)

  def update(self, delta):
    self.stheta = math.sin(self.theta)
    self.ctheta = math.cos(self.theta)
    self.vx = -math.cos(self.theta) * self.speed
    self.vy = -math.sin(self.theta) * self.speed
    self.x += self.vx * delta
    self.y += self.vy * delta

    if self.cockpit:
      self.cockpit.x = self.x + self.chairX * self.ctheta - self.chairY * self.stheta
      self.cockpit.y = self.y + self.chairY * self.ctheta + self.chairX * self.stheta

  def draw(self):
    for i, tile in enumerate(self.tiles):
      if tile == 1:
        renderer.world_circle(self.x + i * 10, self.y, 5, (0, 0, 255))


class SmallEnemyShip(WorldObject):
  def __init__(self, x, y):
    super().__init__(x, y)
    objsWithHP.append(self)
    self.img = renderer.load_image('enemy-0.png')
    self.theta = random.random() * math.pi * 2
    self.hp = 10
    self.size = 8
    self.shootCooldown = self.shootReset = 2
    self.speed = 20
    self.target = None
    self.targetCooldown = self.targetReset = 5
    self.turnSpeed = 0.75
    
  def destroy(self):
    pass

  def update(self, delta):
    self.shootCooldown -= delta
    if self.shootCooldown < 0:
      self.shootCooldown = self.shootReset
      dx = math.cos(self.theta) * 0.5
      dy = math.sin(self.theta) * 0.5
      LaserBeam(self.x + dx, self.y + dy, self.theta, self)
      LaserBeam(self.x - dx, self.y - dy, self.theta, self)
    
    
    # Every 5 seconds, find a new target
    self.targetCooldown -= delta
    if self.targetCooldown < 0:
      self.targetCooldown = self.targetReset
      candidates = list(filter(lambda obj: isinstance(obj, AllianceShip), objsWithHP))
      self.target = None if len(candidates) == 0 else random.choice(candidates)
      
    # Head towards the target
    if self.target:
      angleWithTarget = math.atan2(self.target.y - self.y, self.target.x - self.x)
      angleDiff = angleWithTarget - self.theta
      if angleDiff > math.pi:
        self.theta -= math.pi * 2
      elif angleDiff < -math.pi:
        self.theta += math.pi * 2
      if abs(angleDiff) > self.turnSpeed * delta:
        if angleDiff > 0:
          self.theta += self.turnSpeed * delta
        else:
          self.theta -= self.turnSpeed * delta
          
        
      
    # Movement
    self.x += math.cos(self.theta) * self.speed * delta
    self.y += math.sin(self.theta) * self.speed * delta
    
          

  def draw(self):
    renderer.world_circle(self.x, self.y, self.size, '#FF0000') # debug circle
    renderer.world_img_rot(self.img, self.x, self.y, self.size, self.theta)
    pass


class CollisionWall(WorldObject):
  def __init__(self, x, y, x2=0, y2=0):
    super().__init__(x, y)
    walls.append(self)
    self.x2 = x2
    self.y2 = y2
    if self.x2 < self.x:
      self.x, self.x2 = self.x2, self.x
    if self.y2 < self.y:
      self.y, self.y2 = self.y2, self.y

  def update(self, delta):
    pass

  def draw(self):
    renderer.world_line(self.x, self.y, self.x2, self.y2, '#060270', 0.1)


class TurretStation(WorldObject):
  def __init__(self, x, y, targetInstance=SmallEnemyShip):
    super().__init__(x, y)
    self.radius = 0.85
    self.color = '#4030e0'
    self.controls = None
    for obj in objs:
      if isinstance(obj, Turret) and obj.station == None:
        self.controls = obj
        obj.station = self
        break
    self.image = renderer.load_image('turret-station.png')
    self.cockpit = None
    self.size = 1
    
    self.shootCooldown = 0
    self.shootCooldownMax = 0.1
    self.targetX = 0
    self.targetY = 0
    self.theta = 0
    self.theta2 = 0
    self.gotoTargetX = 0
    self.gotoTargetY = 0
    self.maxCamHt = 1.5
    self.target = None
    self.targetInstance = targetInstance
    self.targetCooldown = self.targetReset = 3.7

  def update(self, delta):
    self.shootCooldown -= delta
    
    if self.cockpit == None: # If AI-controlled
      self.targetCooldown -= delta
      if self.targetCooldown < 0:
        if random.random() < 0.75: # 3/4 chance to target nothing
          self.target = None
          self.targetCooldown = self.targetReset * random.random()
        else:
          self.targetCooldown = self.targetReset
          candidates = list(filter(lambda obj: isinstance(obj, self.targetInstance), objsWithHP))
          if len(candidates) > 0:
            self.target = random.choice(list(candidates))
          else:
            self.target = None
            
      if self.target and self.controls:
        self.theta2 = math.atan2(self.target.y - self.controls.y, self.target.x - self.controls.x)
        if self.shootCooldown < 0:
          self.shootCooldown = self.shootCooldownMax
          LaserBeam(self.controls.x, self.controls.y, self.theta2, self)
    
      
      
  
  def player_control(self, delta):
    
    distFromTurret = max(0, window['width']*3/4 - mouse['x'] ) / window['width'] * 850
    self.theta = math.pi-(mouse['y'] / window['height'] - 0.5) * 2.5
    self.gotoTargetX = self.controls.x + distFromTurret * math.cos(self.theta)
    self.gotoTargetY = self.controls.y + distFromTurret * math.sin(self.theta)
    self.targetX += (self.gotoTargetX - self.targetX) * 0.2
    self.targetY += (self.gotoTargetY - self.targetY) * 0.2
    self.theta2 = math.atan2(renderer.RevY(mouse['y']) - self.controls.y, renderer.RevX(mouse['x']) - self.controls.x)

    
    if mouse['left']:
      if self.shootCooldown < 0 and self.controls.x > renderer.RevX(mouse['x']):
        self.shootCooldown = self.shootCooldownMax
        
        LaserBeam(self.controls.x, self.controls.y, self.theta2, self)        
        

    
    # Jump out
    elif keys.get('Return', False):
      global me
      keys['Return'] = False
      me = self.cockpit
      me.y += self.size / 2

  def draw(self):
    renderer.world_img(self.image, self.x - self.size/2, self.y - self.size/2, self.size)


class Turret(WorldObject):
  def __init__(self, x, y):
    super().__init__(x, y)
    self.theta = 0
    self.radius = 1.45
    self.color = '#777777'
    self.station = None
    self.img = renderer.load_image('tile-ap.png')
    self.size = 20

  def update(self, delta):
    if self.station:
      self.theta = self.station.theta2
    

  def draw(self):
    renderer.world_circle(self.x, self.y, self.radius, self.color)
    
    sx = math.cos(self.theta)
    sy = math.sin(self.theta)
    
    
    # # Turret barrel
    barrel_length = 1.7
    barrel_width = 0.1
    barrel_x = self.x + sx * barrel_length
    barrel_y = self.y + sy * barrel_length
    renderer.world_line(self.x, self.y, barrel_x,
                        barrel_y, '#445', barrel_width)
    
    # Turret base (elongated at back side)
    base_length = 0.5
    base_width = 0.7
    barrel_x = self.x + sx * base_length
    barrel_y = self.y + sy * base_length
    barrel_x2 = self.x - sx * base_length
    barrel_y2 = self.y - sy * base_length
    renderer.world_line(barrel_x2, barrel_y2, barrel_x, barrel_y, '#333', base_width)
    
    
    # renderer.world_polygon([
    #   (self.x - sx * base_length, self.y - sy * base_length),
    #   (self.x + sx * base_length, self.y + sy * base_length),
    #   (self.x + sx * base_length - sx * base_width, self.y + sy * base_length - sy * base_width),
    #   (self.x - sx * base_length - sx * base_width, self.y - sy * base_length - sy * base_width),
    # ], 'black')
    
    # renderer.world_img_rot(self.img, self.x-.5, self.y-.5, 2, self.theta)



class AllianceMotherShip(WorldObject):
  def __init__(self, x, y, s=1, sx=1):
    super().__init__(x, y)
    self.name = 'MotherShip'
    self.size = s
    self.size2 = sx
    self.points = [
      (0, -s * 1.1),
      (sx, -s),
      (sx, s),
      (0, s * 1.1),
      (-sx, s),
      (-sx, -s),
    ]
    self.color = 'gray'
    self.spawnShipCooldown = self.spawnShipReset = 1 # respawn instantly

  def updatePoints(self):
    s = self.size
    sx = self.size2
    self.points = [
      (0, -s * 1.1),
      (sx, -s),
      (sx, s),
      (0, s * 1.1),
      (-sx, s),
      (-sx, -s),
    ]

  def update(self, delta):
    # Every second, check if there are less than 2 alliance ships and spawn one if so 
    if gameManager.scene_name == 'game':  
      self.spawnShipCooldown -= delta
      if self.spawnShipCooldown < 0:
        self.spawnShipCooldown = self.spawnShipReset
        if len(list(filter(lambda obj: isinstance(obj, AllianceShip), objsWithHP))) < 2:
          AllianceShip(self.x - 16, self.y + 7 + random.random() * 20)

  def draw(self):
    renderer.world_polygon(
      [(self.x + dx, self.y + dy) for dx, dy in self.points], self.color
    )


class EnemyMotherShip(WorldObject):
  def __init__(self, x, y, s=1):
    super().__init__(x, y)
    self.name = 'EnemyMotherShip'
    self.size = s
    self.points = [
      (0, -s * 1.5),
      (s * 1.1, -s * 1.1),
      (s * 1.5, 0),
      (s * 1.1, s * 1.1),
      (0, s * 1.5),
      (-s * 1.1, s * 1.1),
      (-s * 1.5, 0),
      (-s * 1.1, -s * 1.1),
    ]
    self.color = 'gray'
    self.spawnShipCooldown = self.spawnShipReset = 30
    self.start = False
    

  def updatePoints(self):
    s = self.size
    self.points = [
      (0, -s * 1.5),
      (s * 1.1, -s * 1.1),
      (s * 1.5, 0),
      (s * 1.1, s * 1.1),
      (0, s * 1.5),
      (-s * 1.1, s * 1.1),
      (-s * 1.5, 0),
      (-s * 1.1, -s * 1.1),
    ]

  def update(self, delta):
    if gameManager.scene_name == 'game':  
      if len(objsWithHP) < 10:
        if self.start:
          for i in range(8):
            SmallEnemyShip(self.x, self.y)
          self.start = False
        self.spawnShipCooldown -= delta
        if self.spawnShipCooldown < 0:
          self.spawnShipCooldown = self.spawnShipReset
          # Spawn a small enemy ship
          SmallEnemyShip(self.x, self.y)

  def draw(self):
    renderer.world_polygon(
      [(self.x + dx, self.y + dy) for dx, dy in self.points], self.color
    )


class Bird(WorldObject):
  def __init__(self, x, y, img="bird.png", flipped=False):
    super().__init__(x, y)
    self.color = (255, 255, 0)  # Yellow color
    self.size = 0.65
    self.img = renderer.load_image(img)
    self.speed = 4
    self.flipped = flipped
    self.nearestShip = None
    self.insideTileX = 0
    self.insideTileY = 0
    self.isNearDoor = False
    self.lastX = x
    self.lastY = y
    self.maxCamHt = 0.04
    self.follower = None # Bird object that follows this bird
    self.followerDistance = 1

  def revertPosition(self):
    # Revert the position of the bird to the last position
    self.x = self.lastX
    self.y = self.lastY

  def player_control(self, delta):
    self.lastX = self.x
    self.lastY = self.y
    vx = 0
    vy = 0
    if keys.get('w', False):
      vy -= self.speed * delta
    if keys.get('s', False):
      vy += self.speed * delta
    if keys.get('a', False):
      vx -= self.speed * delta
      self.flipped = False
    if keys.get('d', False):
      vx += self.speed * delta
      self.flipped = True
    if keys.get('Shift_L', False):
      self.speed = 50 # for debuggin
      
    if abs(vx) and abs(vy):
      vx *= math.sqrt(2) / 2
      vy *= math.sqrt(2) / 2
    
    self.x += vx
    self.y += vy
    if keys.get('Return', False) and self.nearestShip:
      # Entering the ship
      keys['Return'] = False
      # self.x = self.nearestShip.chairX
      # self.y = self.nearestShip.chairY
      global me
      me = self.nearestShip
      self.x = me.x
      self.y = me.y
      self.nearestShip.cockpit = self
        
    if self.follower: # If bird has follower, move the follower towards the bird, keeping the angle but targetting a certain distance
      # Calculate the angle between the two birds
      dx = self.x - self.follower.x
      dy = self.y - self.follower.y
      angle = math.atan2(dy, dx)
      currentDistance = math.sqrt(dx**2 + dy**2)
      targetDistance = self.followerDistance
      direction = 1 if currentDistance > targetDistance else 0
      self.follower.x += math.cos(angle) * self.speed * 0.8 * direction * delta
      self.follower.y += math.sin(angle) * self.speed * 0.8 * direction * delta
      self.follower.flipped = dx > 0
      

  def update(self, delta):
    # if self.insideTile and self.insideTile.parent and not self.insideTile.parent.cockpit:
    # if self.nearestShip:
    #   self.x += self.nearestShip.vx * delta
    #   self.y += self.nearestShip.vy * delta

    self.nearestShip = None
    minDist = 1000
    for obj in objs:
      if isinstance(obj, AllianceShip) or isinstance(obj, TurretStation):
        dist = math.dist((self.x, self.y), (obj.x, obj.y))
        if dist < minDist and dist < 3:
          minDist = dist
          self.nearestShip = obj

    # # For nearest ship calculate the tile x and y
    # if self.nearestShip:
    #   # Transform the coordinates to the ship's coordinates
    #   x = self.x - self.nearestShip.x
    #   y = self.y - self.nearestShip.y
    #   self.insideTileX = x * self.nearestShip.ctheta + y * self.nearestShip.stheta
    #   self.insideTileY = y * self.nearestShip.ctheta - x * self.nearestShip.stheta
    #   # print(f"Inside tile: {self.insideTileX}, {self.insideTileY}")

    #   # Check if bird is close to the tile's outline. If so, "push" the bird back perpendicular to the tile's outline
    # if self.nearestShip and not self.isNearDoor:
    #   tolerance = self.size * 0.5
    #   insideTile = False
    #   ix = math.floor(self.insideTileX)
    #   iy = math.floor(self.insideTileY)
    #   # print(f"Tile: {ix}, {iy}")
    #   if iy % 2 == 1:
    #     ix -= 1
    #     self.insideTileX -= 1
    #   for tile in self.nearestShip.tiles:
    #     if tile.y == iy and (tile.x == ix or tile.x == ix + 1):
    #       insideTile = True
    #       break
    #   if insideTile:
    #     fx = 0
    #     if self.insideTileX % 2 < tolerance:
    #       fx = 1
    #     elif self.insideTileX % 2 > 2 - tolerance:
    #       fx = -1
    #     fy = 0
    #     if self.insideTileY % 1 < tolerance:
    #       fy = 1
    #     elif self.insideTileY % 1 > 1 - tolerance:
    #       fy = -1
    #     if fx != 0 or fy != 0:
    #       # Rotate the vector to the ship's coordinates
    #       fx = fx * self.nearestShip.ctheta - fy * self.nearestShip.stheta
    #       fy = fy * self.nearestShip.ctheta + fx * self.nearestShip.stheta
    #       # Move the bird back
    #       self.revertPosition()
    # self.isNearDoor = False

    # Collision with walls
    for wall in walls:
      if wall.x == wall.x2:  # Vertical wall
        # If bird is above or below the wall, ignore
        if self.y + self.size <= wall.y or self.y >= wall.y2:
          continue
        # If bird is inside the wall, push it back
        if self.x + self.size > wall.x and self.x - self.size < wall.x:
          if self.x < wall.x:
            self.x = wall.x - self.size
          else:
            self.x = wall.x + self.size
      else:
        # If bird is left or right of the wall, ignore
        if self.x + self.size <= wall.x or self.x >= wall.x2:
          continue
        # If bird is inside the wall, push it back
        if self.y + self.size > wall.y and self.y - self.size < wall.y:
          if self.y < wall.y:
            self.y = wall.y - self.size
          else:
            self.y = wall.y + self.size




  def draw(self):
    func = renderer.world_img_flipped if self.flipped else renderer.world_img
    func(self.img, self.x - self.size / 2, self.y - self.size / 2, self.size)

    # renderer.img(self.img, self.x, self.y, self.size)


class Decoration(WorldObject):
  def __init__(self, x, y, decorIndex=0):
    super().__init__(x, y)
    self.decorIndex = decorIndex
    self.image = renderer.load_image(f'decor-{decorIndex}.png')
    self.size = 1

  def update(self, delta):
    pass

  def updatePoints(self):
    self.decorIndex = min(max(0, self.decorIndex), 3)
    self.image = renderer.load_image(f'decor-{self.decorIndex}.png')

  def draw(self):
    renderer.world_img(self.image, self.x - self.size / 2,
                       self.y - self.size / 2, self.size)


class RectRoom(WorldObject):
  def __init__(self, x, y, x2=None, y2=None):
    super().__init__(x, y)
    self.x2 = x2
    self.y2 = y2
    self.color = '#333'

  def update(self, delta):
    pass

  def updatePoints(self):
    if self.x2 < self.x:
      self.x, self.x2 = self.x2, self.x
    if self.y2 < self.y:
      self.y, self.y2 = self.y2, self.y

  def draw(self):

    if self.x2 == None:
      renderer.world_rect(self.x, self.y, 1, 1, self.color)
    else:
      renderer.world_rect(self.x, self.y, self.x2 - self.x,
                          self.y2 - self.y, self.color)


class StoryController:
  def __init__(self):
    objs.append(self)
    self.storyStep = 0
    self.inDialog = True
    self.currentDialog = []
    self.startDialog = [
      ["bird2", "Welcome to Birds in Space!"],
      ["me", "Where am I?"],
      ["bird2", "You are on our home ship.\nWe are in the middle of an expansive\nspace battle.\nWe need your help to win."],
      ["me", "My help?"],
      ["bird2", "Yes. You were unfrozen from\ncryostasis."],
      ["me", "Huh?"],
      ["bird2", "Don't you remember?"],
      ["me", "Not really..."],
      ["bird2", "Well then, we are all going to die."],
      ["system", "Use the <WASD> keys to move.\nExplore your surroundings.\nDefeat the octagon-shaped enemy\nspaceship."],
    ]
    self.bookDialog = [
      ["system", "You can't win this battle alone."],
      ["system", "Tip: You can talk to other birds\nby pressing <Space> when nearby."],
    ]
    self.askForHelpDialog = [
      ["me", "Please help me out."],
      ["bird2", "Why?"],
      ["me", "Because two is tougher than one."],
      ["bird2", "???"],
      ["me", "I know, it's corny but it's our ONLY\nchance at winning this battle..."],
      ["bird2", "Fine - but this better work."],
      ["system", "Albert is now your companion.\nAlbert will now follow you and help\nyou in space battles."]
    ]
    self.hangarInfoDialog = [
      ["bird2", "This is the hangar.\nEnter a ship using the <Enter> key."],
    ]
    self.endDialog = [
      ["bird2", "We won! Two is tougher!"],
      ["system", "You have won the battle."]
    ]
    self.setCurrentDialog(self.startDialog)
    self.stage = "EXPLORE"
    self.interactedWithBook = False

  def setCurrentDialog(self, dialogObj, hintText="Click to advance story"):
    hud.setHintText(hintText)
    self.currentDialog = dialogObj
    self.storyStep = 0
    self.inDialog = True

  def update(self, delta):
    if self.inDialog:
      if mouse['left']:
        mouse['left'] = False
        self.storyStep += 1
        if self.storyStep > len(self.currentDialog) - 1:
          self.inDialog = False
          hud.setHintText("")
          
    if self.stage == 'EXPLORE':
      # Collision/interaction with the book
      if math.dist((me.x, me.y), (bookOfAnswers.x, bookOfAnswers.y)) < 2:
        if not self.interactedWithBook:
          hud.setHintText("Press <Space> to interact")
        if keys.get('space', False):
          self.interactedWithBook = True
          keys['space'] = False
          self.setCurrentDialog(
            self.bookDialog, "Click to turn to the next page")
          
      # Interaction with bird2
      elif math.dist((me.x, me.y), (bird2.x, bird2.y)) < 2:
        if self.interactedWithBook:
          hud.setHintText("Press <Space> to ask for help")
        if keys.get('space', False):
          self.interactedWithBook = True
          keys['space'] = False
          self.setCurrentDialog(
            self.askForHelpDialog, "Click to advance story")
          me.follower = bird2
          self.stage = 'PRE-BATTLE-1'
          
      else:
        hud.setHintText("")
    
    elif self.stage == 'PRE-BATTLE-1':
      if me.x >= -13 and me.y >= -20 and me.x <= -8 and me.y <= -13:
        self.stage = 'PRE-BATTLE-2'
        self.setCurrentDialog(
          self.hangarInfoDialog, "Click to advance story")
        me.follower = None
    
    elif self.stage == 'PRE-BATTLE-2':
      s2 = objsWithHP[0]
      bird2.x += (s2.x - bird2.x) * 0.1
      bird2.y += (s2.y - bird2.y) * 0.1
      if math.dist((bird2.x, bird2.y), (s2.x, s2.y)) < 0.001:
        self.stage = 'BATTLE'
      me.x = me.lastX # freeze player
      me.y = me.lastY
      
        
    elif self.stage == 'BATTLE':
      s2 = objsWithHP[0]
      bird2.x = s2.x + 0.5
      bird2.y = s2.y + 0.5
      s2.speed = s2.maxSpeed * 0.5
      
      pass
      
      

  def draw(self):
    if self.inDialog:
      speaker = self.currentDialog[self.storyStep][0]
      text = self.currentDialog[self.storyStep][1]
      target = None

      # Draw text box at bottom
      renderer.rect_outlined(
        10, window['height'] - 150, window['width'] - 20, window['height'] - 30, 'white', 'black')
      renderer.text_dialog(20, window['height'] - 140, text, 'black')

      # Triangle part of speech bubble
      if speaker == 'me' or speaker == 'bird2':
        w = (1 if speaker == 'me' else 2) * window['width'] / 3
        h = window['height'] - 150
        target = me if speaker == 'me' else bird2
        renderer.tri_outlined(
          w - 10, h, w + 10, h, renderer.X(target.x), renderer.Y(target.y + target.size * 0.75), 'white', 'black')
        renderer.line(w - 10, h, w + 10, h, 'white', 2)


class LevelEditor:
  def __init__(self):
    self.options = [
      # Name, image, class, arg1, arg2
      ['Bird', 'bird.png', Bird],
      ['Ally Mothership', None, AllianceMotherShip, 'y-size', 'x-size2'],
      ['Enemy Mothership', None, EnemyMotherShip, 'x-size'],
      ['Ally Ship', None, AllianceShip],
      ['Enemy Ship', 'enemy-0.png', SmallEnemyShip],
      ['Collision', None, CollisionWall, 'xy-x2-y2'],
      ['Decor', 'decor-0.png', Decoration, 'y-decorIndex'],
      ['Rect. Room', None, RectRoom, 'xy-x2-y2'],
      ['Turret Station', 'turret-station.png', TurretStation],
      ['Turret', 'turret.png', Turret],
      ['Sheilds', None, Shields, 'x-w', 'y-h'],


    ]
    for o in self.options:
      if o[1] != None:
        o[1] = renderer.load_image(o[1])
    self.mode = "none"  # "none"|"placing"
    self.hovering = -1
    self.ghost = None
    self.argStep = 0

  def update(self, delta):
    if keys.get('p', False):
      print('# Level code:')
      keys['p'] = False
      for obj in objs:
        corrospondingOp = None
        for op in self.options:
          if obj.__class__ == op[2]:
            corrospondingOp = op
            break
        if corrospondingOp:
          print(f"{op[2].__name__}({obj.x}, {obj.y}", end="")
          args = corrospondingOp[3:]
          for arg in args:
            argParts = arg.split('-')
            if len(argParts) > 2:
              arg1 = argParts[1]
              arg2 = argParts[2]
              if hasattr(obj, arg1):
                print(f", {getattr(obj, arg1)}", end="")
              if hasattr(obj, arg2):
                print(f", {getattr(obj, arg2)}", end="")
            else:
              arg1 = argParts[1]
              print(f", {getattr(obj, arg1)}", end="")
          print(")")

    pass

  def draw(self):

    # Draw a grid over everything
    x1 = x1s = math.floor(renderer.RevX(0))
    y1 = math.floor(renderer.RevY(0))
    x2 = math.floor(renderer.RevX(window['width']))
    y2 = math.floor(renderer.RevY(window['height']))
    gridlineWidth = 1
    while x1 < x2:
      renderer.world_line(x1, y1, x1, y2, '#222', renderer.RevS(gridlineWidth))
      x1 += 4
    x1 = x1s
    while y1 < y2:
      renderer.world_line(x1, y1, x2, y1, '#222', renderer.RevS(gridlineWidth))
      y1 += 4

    op = self.options[self.hovering]
    if self.mode == "none":
      pass
    elif self.mode == "placing":
      if self.argStep == 0:
        self.ghost.x = round(renderer.RevX(mouse['x']))
        self.ghost.y = round(renderer.RevY(mouse['y']))
        renderer.text(
          10, 140, f"Click to place\nX: {self.ghost.x}\nY: {self.ghost.y}", 'white')
      else:
        # print(op, self.argStep)
        dir, arg, *arg2 = op[self.argStep + 2].split("-")
        s = 0
        s2 = 0
        if len(arg2) > 0:
          arg2 = arg2[0]
        if dir == 'x':
          s = round(renderer.RevX(mouse['x']) - self.ghost.x)
          setattr(self.ghost, arg, s)
          renderer.text(
            10, 140, f"Click to set argument\nDirection: {dir}\nArgument: {arg}\nValue: {s}", 'white')
        elif dir == 'y':
          s = round(renderer.RevY(mouse['y']) - self.ghost.y)
          setattr(self.ghost, arg, s)
          renderer.text(
            10, 140, f"Click to set argument\nDirection: {dir}\nArgument: {arg}\nValue: {s}", 'white')
        elif dir == 'xy':
          s = round(renderer.RevX(mouse['x']))
          s2 = round(renderer.RevY(mouse['y']))
          # print(s, s2, arg, arg2)
          setattr(self.ghost, arg, s)
          setattr(self.ghost, arg2, s2)
          renderer.text(
            10, 140, f"Click to set argument\nDirection: {dir}\nArgument: {arg}, {arg2}\nValue: {s}, {s2}", 'white')

        if hasattr(self.ghost, 'updatePoints'):
          self.ghost.updatePoints()

      if mouse['left']:
        mouse['left'] = False
        # print(len(op)-3, self.argStep)
        if len(op) - 3 > self.argStep:  # keep going
          self.argStep += 1
        else:
          self.mode = "none"
          self.ghost = None
          self.argStep = 0
      elif mouse['right']:
        self.mode = "none"
        self.ghost = None
        self.argStep = 0

      # Menu options on right side
    x = window['width'] - 50
    renderer.rect_outlined(
      window['width'] - 100, 5, window['width'] - 5, window['height'] - 5, 'black', 'white')
    y = 50
    for i in range(len(self.options)):
      option = self.options[i]
      if self.mode == 'none' and mouse['x'] > x - 26 and mouse['x'] < x + 26 and mouse['y'] > y - 26 and mouse['y'] < y + 26:
        self.hovering = i

        mouse['cursor'] = 'hand2'
        if self.mode == 'none' and mouse['left']:
          mouse['left'] = False
          self.mode = 'placing'
          self.ghost = option[2](0, 0)

        renderer.rect(x - 22, y - 22, x + 22, y + 22, '#1a1')
      else:
        renderer.rect(x - 22, y - 22, x + 22, y + 22, '#222')
      if option[1]:
        renderer.img(option[1], x - 10, y - 10, 20)
      renderer.text_center(x, y - 17, option[0], 'white')
      # Show how many options are available
      if len(option) > 3:
        renderer.text_center(
          x + 6, y + 17, f'+{len(option) - 3} args', 'white')
      y += 50


# Constants
FPS = 30  # Frames per second

####### Classes and global vars ########


# Define root
root = tk.Tk()

# Define mouse position and keys down
mouse = {'x': 0, 'y': 0, 'left': False,
         'right': False, 'middle': False, 'scroll': 0, 'cursor': 'arrow'}
keys = {}
window = {
  'width': 600,
  'height': 600
}
me = None
bird2 = None
bookOfAnswers = None

# Define renderer
renderer = renderer.Renderer(root, window)
le = LevelEditor()


class DebugCircle():
  def __init__(self):
    objs.append(self)
    self.x, self.y = random.random() * 5, random.random() * 5
    self.r = random.random()
    self.color = (random.randint(0, 255), random.randint(
        0, 255), random.randint(0, 255))

  def update(self, delta):
    self.x += delta * 10
    if (self.x > window['width'] * 1.25):
      self.x -= window['height'] * 1.5

  def draw(self):

    # Draw the circle on the renderer
    renderer.world_circle(self.x, self.y, self.r, self.color)

# Define UI elements


class MenuText:
  def __init__(self, x, y, text, color, isVeryLarge=False):
    objs.append(self)
    self.text = text
    self.x = x
    self.y = y
    self.relativeX = x - window['width'] / 2
    self.relativeY = y - window['height'] / 2
    self.color = color
    self.isVeryLarge = isVeryLarge

  def update(self, delta):
    pass

  def draw(self):
    if self.isVeryLarge:
      renderer.text_center_very_large(self.x, self.y, self.text, self.color)
    else:
      renderer.text_center(self.x, self.y, self.text, self.color)

  def resize(self):
    self.x = window['width'] / 2 + self.relativeX
    self.y = window['height'] / 2 + self.relativeY


class MenuOption:
  def __init__(self, text, x, y, command):
    objs.append(self)
    self.text = text
    self.x = x
    self.y = y
    self.w = 100
    self.h = 20
    self.relativeX = x - window['width'] / 2
    self.relativeY = y - window['height'] / 2
    self.command = command
    self.hover = False

  def update(self, delta):
    if mouse['x'] > self.x - self.w / 2 and mouse['x'] < self.x + self.w / 2 and \
            mouse['y'] > self.y - self.h / 2 and mouse['y'] < self.y + self.h / 2:
      self.hover = True
      mouse['cursor'] = 'hand2'
    else:
      self.hover = False
    if self.hover and mouse['left']:
      self.command()
      mouse['left'] = False  # Prevent multiple clicks

  def draw(self):
    colors = ['black', 'white']
    if self.hover:
      colors = ['#111', 'limegreen']

    renderer.rect_outlined(self.x - self.w / 2, self.y - self.h / 2,
                           self.x + self.w / 2, self.y + self.h / 2, colors[0], colors[1])
    renderer.text_center(self.x, self.y, self.text, "white")

  def resize(self):
    self.x = window['width'] / 2 + self.relativeX
    self.y = window['height'] / 2 + self.relativeY


# Define HUD elements
class HUD:
  def __init__(self):
    self.hintText = ""  # text that appears at the bottom e.g. "Press <Enter> to control ship"

  def setHintText(self, hintText):
    self.hintText = hintText

  def update(self, delta):
    pass

  def draw(self):
    # Draw the hint text at the bottom of the screen
    renderer.text_center_large(window['width'] / 2,
                               window['height'] - 15, self.hintText, "white")


hud = HUD()

# Define game manager


class GameManager:

  def __init__(self, root):
    self.root = root
    self.resize_job = None
    self.scene_name = None

  # Thanks to GitHub Copilot
  def on_possible_resize(self, event):
    if self.resize_job:
      self.root.after_cancel(self.resize_job)
    self.resize_job = self.root.after(
        200, lambda: self.on_certain_resize(event))

  def on_certain_resize(self, event):
    renderer.on_window_resize(event)
    for obj in objs:
      if hasattr(obj, 'resize'):
        obj.resize()

  def change_scene(self, scene):
    if self.scene_name == scene:
      return
    self.scene_name = scene
    objs.clear()
    w = window['width']
    h = window['height']
    if scene == "menu":
      MenuText(w / 2, h / 2 - 120, "Birds in Space", "#98F5F9", True)
      MenuOption("Start Game", w / 2, h / 2 - 20,
                 lambda: self.change_scene("game"))
      MenuOption("Level Editor", w / 2, h / 2 + 30,
                 lambda: self.change_scene("level_editor"))
      MenuOption("Credits", w / 2, h / 2 + 80,
                 lambda: self.change_scene("credits"))
      MenuOption("Exit", w / 2, h / 2 + 130, lambda: self.root.quit())
    elif scene == "game":

      # Game init
      for i in range(100):
        DebugCircle()

      AllianceMotherShip(0, -12, 50, 25)
      RectRoom(-23, -60, 22, -51)
      RectRoom(-1, -51, 2, 27)
      RectRoom(-16, 27, 16, 36)
      RectRoom(-19, 12, -8, 22)
      RectRoom(-8, 12, -1, 14)
      RectRoom(-25, -23, -8, 8)
      RectRoom(-8, -18, -1, -16)
      CollisionWall(-25, -23, -8, -23)
      CollisionWall(-8, -23, -8, -18)
      CollisionWall(-8, -18, -1, -18)
      CollisionWall(-1, -18, -1, -51)
      CollisionWall(-1, -51, -23, -51)
      CollisionWall(-23, -51, -23, -60)
      CollisionWall(-23, -60, 22, -60)
      CollisionWall(22, -60, 22, -51)
      CollisionWall(22, -51, 2, -51)
      CollisionWall(2, -51, 2, 27)
      CollisionWall(2, 27, 16, 27)
      CollisionWall(16, 27, 16, 36)
      CollisionWall(16, 36, -16, 36)
      CollisionWall(-16, 36, -16, 27)
      CollisionWall(-16, 27, -1, 27)
      CollisionWall(-1, 27, -1, 14)
      CollisionWall(-1, 14, -8, 14)
      CollisionWall(-8, 14, -8, 22)
      CollisionWall(-8, 22, -19, 22)
      CollisionWall(-19, 22, -19, 12)
      CollisionWall(-19, 12, -1, 12)
      CollisionWall(-1, 12, -1, -16)
      CollisionWall(-1, -16, -8, -16)
      CollisionWall(-8, -16, -8, 8)
      CollisionWall(-8, 8, -25, 8)
      Turret(-22, -27)
      Turret(-22, 12)
      Turret(-22, -48)
      Turret(-22, 32)
      TurretStation(-18, -58)
      TurretStation(-10, -58)
      TurretStation(11, -58)
      TurretStation(18, -58)
      Decoration(-9, 21, 0)
      Decoration(-18, 21, 0)
      global me
      # me = Bird(-18, -58)
      me = Bird(-14.0, 20.0, "bird_x.png", True)
      global bird2
      bird2 = Bird(-11.0, 19.0, "bird_y.png")
      EnemyMotherShip(-582, -24, 22)
      Turret(-554, -24)
      Turret(-563, -46)
      Turret(-563, -2)
      TurretStation(99999, -58, AllianceShip)
      TurretStation(99999, -58, AllianceShip)
      TurretStation(99999, -58, AllianceShip)
      AllianceShip(-21.0, -17.0)
      AllianceShip(-19.0, -1.0)
      Shields(0, -12, 40, 68)
      Shields(-582, -24, 36, 36)
      global bookOfAnswers
      bookOfAnswers = Decoration(14, 33, 3)
      global storyController
      storyController = StoryController()

      # me = Bird(0.1, 0.1)

    elif scene == "level_editor":
      for i in range(5):
        DebugCircle()
      AllianceMotherShip(0, -12, 50, 25)
      RectRoom(-23, -60, 22, -51)
      RectRoom(-1, -51, 2, 27)
      RectRoom(-16, 27, 16, 36)
      RectRoom(-19, 12, -8, 22)
      RectRoom(-8, 12, -1, 14)
      RectRoom(-25, -23, -8, 8)
      RectRoom(-8, -18, -1, -16)
      CollisionWall(-25, -23, -8, -23)
      CollisionWall(-8, -23, -8, -18)
      CollisionWall(-8, -18, -1, -18)
      CollisionWall(-1, -18, -1, -51)
      CollisionWall(-1, -51, -23, -51)
      CollisionWall(-23, -51, -23, -60)
      CollisionWall(-23, -60, 22, -60)
      CollisionWall(22, -60, 22, -51)
      CollisionWall(22, -51, 2, -51)
      CollisionWall(2, -51, 2, 27)
      CollisionWall(2, 27, 16, 27)
      CollisionWall(16, 27, 16, 36)
      CollisionWall(16, 36, -16, 36)
      CollisionWall(-16, 36, -16, 27)
      CollisionWall(-16, 27, -1, 27)
      CollisionWall(-1, 27, -1, 14)
      CollisionWall(-1, 14, -8, 14)
      CollisionWall(-8, 14, -8, 22)
      CollisionWall(-8, 22, -19, 22)
      CollisionWall(-19, 22, -19, 12)
      CollisionWall(-19, 12, -1, 12)
      CollisionWall(-1, 12, -1, -16)
      CollisionWall(-1, -16, -8, -16)
      CollisionWall(-8, -16, -8, 8)
      CollisionWall(-8, 8, -25, 8)
      TurretStation(-18, -58)
      TurretStation(-10, -58)
      TurretStation(11, -58)
      TurretStation(18, -58)
      Turret(-22, -27)
      Turret(-22, 12)
      Turret(-22, -48)
      Turret(-22, 32)
      Decoration(-9, 21, 0)
      Decoration(-18, 21, 0)
      EnemyMotherShip(-582, -24, 22)
      Turret(-554, -24)
      Turret(-563, -46)
      Turret(-563, -2)
      AllianceShip(-21.0, -17.0)
      AllianceShip(-19.0, -1.0)

    elif scene == "credits":
      MenuOption("Back to Menu", w / 2, h / 2 + 120,
                 lambda: self.change_scene("menu"))
      MenuText(w / 2, h / 2 - 35, "Created by: <unknown>", "white")
      MenuText(w / 2, h / 2 - 15,
               "Special thanks to Loc and the Software Development Club for hosting this hackathon.", "gold")
      MenuText(w / 2, h / 2 + 5,
               "This game was created in 2 weeks in Python and Tkinter.", "white")
      MenuText(w / 2, h / 2 + 25, "Thanks for playing!", "white")

  def preupdate(self):
    mouse['cursor'] = 'arrow'

  def postupdate(self):
    renderer.label.config(cursor=mouse['cursor'])


gameManager = GameManager(root)

# Init, draw, main


def init():
  #

  root.title("|| Birds in Space ||")
  root.geometry(f"{window['width']}x{window['height']}")
  root.bind("<Configure>", gameManager.on_possible_resize)
  root.bind("<Motion>", lambda e: (mouse.update({'x': e.x, 'y': e.y})))
  root.bind("<KeyPress>", lambda e: keys.update({e.keysym: True}))
  root.bind("<KeyRelease>", lambda e: keys.update({e.keysym: False}))
  root.bind("<ButtonPress-1>", lambda e: mouse.update({'left': True}))
  root.bind("<ButtonRelease-1>", lambda e: mouse.update({'left': False}))
  root.bind("<ButtonPress-2>", lambda e: mouse.update({'middle': True}))
  root.bind("<ButtonRelease-2>", lambda e: mouse.update({'middle': False}))
  root.bind("<ButtonPress-3>", lambda e: mouse.update({'right': True}))
  root.bind("<ButtonRelease-3>", lambda e: mouse.update({'right': False}))
  root.bind("<MouseWheel>", lambda e: mouse.update({'scroll': e.delta}))

  root.bind("<Escape>", lambda e: root.quit())
  renderer.label.pack(fill='both', expand=True)
  gameManager.change_scene("menu")


last_time = time.time()


def mainloop():
  global last_time

  # Calculate time delta
  current_time = time.time()
  delta = current_time - last_time
  last_time = current_time

  # Update game state
  gameManager.preupdate()
  if me:
    me.player_control(delta)
  for i in range(len(objs) - 1, -1, -1):
    objs[i].update(delta)
  gameManager.postupdate()
  renderer.update(mouse, keys, me)
  if gameManager.scene_name == "level_editor":
    renderer.levelEditorControls(mouse, keys)
    le.update(delta)
  elif gameManager.scene_name == "game":
    if isinstance(me, TurretStation):
      renderer.camX = me.targetX
      renderer.camY = me.targetY
    else:
      renderer.camX = me.x
      renderer.camY = me.y
  hud.update(delta)
  
  # Remove dead objects
  for i in range(len(objsWithHP) - 1, -1, -1):
    if objsWithHP[i].hp <= 0:
      objsWithHP[i].destroy()
      objs.remove(objsWithHP[i])
      objsWithHP.remove(objsWithHP[i])

  # Draw game state
  renderer.clearScreen()
  for obj in objs:
    obj.draw()
  hud.draw()
  if gameManager.scene_name == "level_editor":
    le.draw()

  # Print debug (FPS)
  if delta > 0:
    renderer.text(10, 10, f"FPS: {1 / delta:.2f}", "white")
  renderer.text(
    10, 30, f"Mouse: {mouse['x']}, {mouse['y']} {mouse['scroll']}", "white")
  keysList = []
  for key in keys:
    if keys[key]:
      keysList.append(key)
  renderer.text(10, 50, f"Keys: {keysList}", "white")
  renderer.text(10, 70, f"Scene: {gameManager.scene_name}", "white")
  renderer.text(10, 90, f"Objects: {len(objs)}", "white")
  renderer.text(
    10, 110, f"Camera: {round(renderer.camX)}, {round(renderer.camY)}, {round(renderer.camHt, 2)}", "white")

  # Update the Tkinter image
  renderer.refreshTkinterImage()

  # Draw next frame in 33 ms
  root.after(20, mainloop)


if __name__ == '__main__':
  init()
  mainloop()
  root.mainloop()
