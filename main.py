'''
Main classes
- GameManager: Manages the game state
- Renderer: Renders shapes and images to the screen
- MenuOption: Small menu option
- DebugCircle: Debug circle object

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
DOOR_THICKNESS = 0.01
DOOR_LENGTH = 0.4
DOOR_OPEN_AMOUNT = 0.8


# Define various objects
objs = []


class WorldObject:
  def __init__(self, x, y):
    objs.append(self)
    self.x = x
    self.y = y

  def update(self, delta):
    raise NotImplementedError("Subclasses should implement this!")

  def draw(self):
    raise NotImplementedError("Subclasses should implement this!")


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
    self.meInside = False
    self.meAdjacent = False

  '''
  position is one of 0=top-left, 1=top-right, 2=right, 3=bottom-right, 4=bottom-left, 5=left
  '''

  def addDoor(self, position):
    doorPosTable = [
      [0.5, DOOR_THICKNESS, False, 1],  # top-left
      [1.5, DOOR_THICKNESS, False, 1],  # top-right
      [2 - DOOR_THICKNESS, 0.5, True, 1],   # right
      [1.5, 1 - DOOR_THICKNESS, False, 1],  # bottom-right
      [0.5, 1 - DOOR_THICKNESS, False, 1],  # bottom-left
      [DOOR_THICKNESS, 0.5, True, 1],   # left
    ]
    self.doors.append(doorPosTable[position])

  def update(self, delta):
    self.ax = self.parent.x + self.x * \
      self.parent.ctheta - self.y * self.parent.stheta
    self.ay = self.parent.y + self.y * \
        self.parent.ctheta + self.x * self.parent.stheta
    dx = me.x - self.ax
    dy = me.y - self.ay
    self.meInside = 0 < dx < 2 and 0 < dy < 1
    if self.meInside:
      me.insideTile = self
    self.meAdjacent = -1 < dx < 3 and -1 < dy < 2

    for door in self.doors:
      if self.meAdjacent and math.dist((me.x, me.y), (self.ax + door[0], self.ay + door[1])) < 0.3:

        door[3] += (0 - door[3]) * 0.5
      else:
        door[3] += (1 - door[3]) * 0.5

  def draw(self):

    # if self.type == 'engine' and self.parent.usingEngines:sa

    renderer.world_rect(self.x - 0.1, self.y - 0.1, 2 + 0.2, 1 + 0.2, 'green')
    # renderer.world_img(self.image, self.ax, self.ay, 2)
    renderer.world_img_rot(self.image, self.ax, self.ay, 2, self.parent.theta)
    for px, py, isVertical, step in self.doors:
      if isVertical:
        renderer.world_rect(self.ax + px - DOOR_THICKNESS, self.ay + py -
                            DOOR_LENGTH, DOOR_THICKNESS * 2, DOOR_LENGTH * step, 'blue')
        renderer.world_rect(self.ax + px - DOOR_THICKNESS, self.ay + py - DOOR_LENGTH *
                            (1 - step), DOOR_THICKNESS * 2, DOOR_LENGTH * step, 'blue')
      else:
        # Left door
        renderer.world_rect(self.ax + px - DOOR_LENGTH, self.ay + py -
                            DOOR_THICKNESS, DOOR_LENGTH * step, DOOR_THICKNESS * 2, 'blue')
        renderer.world_rect(self.ax + px + DOOR_LENGTH * (1 - step), self.ay +
                            py - DOOR_THICKNESS, DOOR_LENGTH * step, DOOR_THICKNESS * 2, 'blue')
    renderer.world_circle(self.ax, self.ay, 0.1, 'limegreen')


class Ship(WorldObject):
  def __init__(self, x, y, name):
    super().__init__(x, y)
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
    self.maxSpeed = 10
    self.acc = 5
    self.usingEngines = False
    self.cockpit = None

  def convertToBasicShip(self):
    for tile in self.tiles:
      objs.remove(tile)
    self.tiles = [
      Tile(self, 2, -2, 'weapon', [4]),
      Tile(self, 1, -1, 'ap', [1, 3, 4]),
      Tile(self, 3, -1, 'engine'),
      Tile(self, 0, 0, 'control', [1, 3]),
      Tile(self, 2, 0, 'ap', [0, 2]),
      Tile(self, 1, 1, 'ap', [0, 3]),
      Tile(self, 3, 1, 'engine'),
      Tile(self, 2, 2, 'weapon', [0]),
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
      renderer.camGotoHt = max(0.05, renderer.camHt / 2)
      self.cockpit = None

    # Update position based on speed

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


class CarrierShip(WorldObject):
  def __init__(self, x, y):
    super().__init__(x, y)
    self.name = 'CarrierShip'
    self.size = s = 200
    sx = s * 2
    self.points = [
      (0, -s),
      (sx * 0.1, -s * 0.9),
      (sx * 0.1, s * 0.9),
      (0, s),
      (-sx * 0.1, s * 0.9),
      (-sx * 0.1, -s * 0.9),
    ]
    self.color = 'gray'

  def update(self, delta):
    pass

  def draw(self):
    renderer.world_polygon(
      [(self.x + dx, self.y + dy) for dx, dy in self.points], self.color
    )


class Bird(WorldObject):
  def __init__(self, x, y):
    super().__init__(x, y)
    self.color = (255, 255, 0)  # Yellow color
    self.size = 0.2
    self.img = renderer.load_image('bird.png')
    self.speed = 1
    self.flipped = False
    self.insideTile = None

  def player_control(self, delta):
    if keys.get('w', False):
      self.y -= self.speed * delta
    if keys.get('s', False):
      self.y += self.speed * delta
    if keys.get('a', False):
      self.x -= self.speed * delta
      self.flipped = False
    if keys.get('d', False):
      self.x += self.speed * delta
      self.flipped = True
    if keys.get('Return', False) and self.insideTile:
      # Entering the ship
      keys['Return'] = False
      self.x = self.insideTile.parent.chairX
      self.y = self.insideTile.parent.chairY
      global me
      me = self.insideTile.parent
      self.insideTile.parent.cockpit = self
      renderer.camGotoHt = max(0.05, renderer.camHt / 2)

    if self.insideTile:
      hud.hintText = "Press <Enter> to control ship"
    else:
      hud.hintText = ""

  def update(self, delta):
    if self.insideTile and self.insideTile.parent and not self.insideTile.parent.cockpit:
      self.x += self.insideTile.parent.vx * delta
      self.y += self.insideTile.parent.vy * delta

  def draw(self):
    func = renderer.world_img_flipped if self.flipped else renderer.world_img
    func(self.img, self.x - self.size / 2, self.y - self.size / 2, self.size)

    # renderer.img(self.img, self.x, self.y, self.size)


class WorldBuilder:
  def __init__(self):
    objs.append(self)
    self.options = [
      {
          'name': 'Bird',
          'class': Bird,
          'img': renderer.load_image('bird.png'),
      },
      {
          'name': 'Ship',
          'class': Ship,
          'img': renderer.load_image('tile-1.png'),
      }
    ]

  def update(self, delta):
    pass

  def draw(self):
    # print('hi')

    x = window['width'] - 200
    y = 100
    for i in range(len(self.options)):
      option = self.options[i]
      renderer.img(option['img'], x, y, 20)
      x += 50


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

# Define renderer
renderer = renderer.Renderer(root, window)


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


class MenuOption:
  def __init__(self, text, x, y, command):
    objs.append(self)
    self.text = text
    self.x = x
    self.y = y
    self.w = 100
    self.h = 20
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
    self.x = window['width'] / 2
    self.y = window['height'] / 2 + (objs.index(self) * 50) - 50


# Define HUD elements
class HUD:
  def __init__(self):
    self.hintText = ""  # text that appears at the bottom e.g. "Press <Enter> to control ship"

  def update(self, delta):
    pass

  def draw(self):
    # Draw the hint text at the bottom of the screen
    renderer.text_center(window['width'] / 2,
                         window['height'] - 20, self.hintText, "white")


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
      MenuOption("Start Game", w / 2, h / 2 - 50,
                 lambda: self.change_scene("game"))
      MenuOption("Level Editor", w / 2, h / 2,
                 lambda: self.change_scene("level_editor"))
      MenuOption("Options", w / 2, h / 2 + 50,
                 lambda: self.change_scene("options"))
      MenuOption("Exit", w / 2, h / 2 + 100, lambda: self.root.quit())
    elif scene == "game":

      # Game init
      for i in range(100):
        DebugCircle()

      CarrierShip(0, 0)
      # for x in range(-10, -5):
      #   for y in range(5, 10):
      #     if x % 2 == y % 2:
      #       Tile(None, x, y, 'ap' if random.random() > 0.5 else 'engine')

      Ship(0, 0, 'My-ship').convertToBasicShip()

      global me
      me = Bird(0, 0)

    elif scene == "level_editor":
      for i in range(50):
        DebugCircle()
      WorldBuilder()

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
  for obj in objs:
    obj.update(delta)
  if me:
    me.player_control(delta)
  gameManager.postupdate()
  renderer.update(mouse, keys)
  if gameManager.scene_name == "level_editor":
    renderer.levelEditorControls(mouse, keys)
  elif gameManager.scene_name == "game":
    renderer.camX = me.x
    renderer.camY = me.y
  hud.update(delta)

  # Draw game state
  renderer.clearScreen()
  for obj in objs:
    obj.draw()
  hud.draw()

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
