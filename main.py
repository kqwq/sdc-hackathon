'''
Main classes
- GameManager: Manages the game state
- Renderer: Renders shapes and images to the screen


Global vars
- root
- gameManager
- renderer
- objs


'''


import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
import random
import time


# Constants
FPS = 30  # Frames per second
WIDTH = 600  # Width of the canvas
HEIGHT = 600  # Height of the canvas

####### Classes and global vars ########

# Define mouse position and keys down
mouse = {'x': 0, 'y': 0, 'left': False,
         'right': False, 'middle': False, 'scroll': 0, 'cursor': 'arrow'}
keys = {}

# Define root
root = tk.Tk()

# Define renderer


class Renderer:
  def __init__(self):
    self.image = Image.new("RGB", (WIDTH, HEIGHT),
                           "black")  # Create a blank image
    self.draw = ImageDraw.Draw(self.image)  # Drawing context
    self.tk_image = ImageTk.PhotoImage(self.image)  # Tkinter image
    self.label = tk.Label(root, image=self.tk_image, bg='#111', border=0)

    self.camX = 0
    self.camY = 0
    self.camHt = 0
    self.hw = WIDTH / 2
    self.hh = HEIGHT / 2

  def on_window_resize(self, event):
    global WIDTH, HEIGHT
    WIDTH = event.width
    HEIGHT = event.height
    self.hw = WIDTH / 2
    self.hh = HEIGHT / 2
    self.image = Image.new("RGB", (WIDTH, HEIGHT), "black")
    self.draw = ImageDraw.Draw(self.image)
    self.tk_image = ImageTk.PhotoImage(self.image)
    self.label.config(image=self.tk_image)


  def clearScreen(self):
    self.image.paste("black", [0, 0, WIDTH, HEIGHT])

  def refreshTkinterImage(self):
    self.tk_image.paste(self.image)  # Update the Tkinter image

  def rect(self, x, y, w, h, color):
    self.draw.rectangle([x, y, w, h], color)

  def rect_outlined(self, x, y, w, h, color, outline):
    self.draw.rectangle([x, y, w, h], fill=color, outline=outline)

  def circle(self, x, y, r, color):
    self.draw.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=color)

  def line(self, x1, y1, x2, y2, color):
    self.draw.line([x1, y1, x2, y2], fill=color)

  def text(self, x, y, text, color):
    self.draw.text((x, y), text, fill=color, align="center", anchor="mm")

  def X(self, x):
    return self.hw + (x - self.camX) * self.camHt

  def Y(self, y):
    return self.hh + (y - self.camY) * self.camHt

  def S(self, s):
    return s * self.camHt

  def RevX(self, x):
    return (x - self.hw) / self.camHt + self.camX

  def RevY(self, y):
    return (y - self.hh) / self.camHt + self.camY

  def RevS(self, s):
    return s / self.camHt


renderer = Renderer()

# Define various objects
objs = []


class CircleCreator():
  def __init__(self):
    self.x, self.y = random.randint(0, WIDTH), random.randint(0, HEIGHT)
    self.r = random.randint(10, 50)
    self.color = (random.randint(0, 255), random.randint(
        0, 255), random.randint(0, 255))

  def update(self, delta):
    self.x += delta * 10
    if (self.x > WIDTH * 1.25):
      self.x -= WIDTH * 1.5

  def draw(self):

    # Draw the circle on the renderer
    renderer.circle(self.x, self.y, self.r, self.color)

# Define UI elements


class MenuOption:
  def __init__(self, text, x, y, command):
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
    renderer.text(self.x, self.y, self.text, "white")

  def resize(self):
    self.x = WIDTH / 2
    self.y = HEIGHT / 2 + (objs.index(self) * 50) - 50


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
    if scene == "menu":
      objs.extend([MenuOption("Start Game", WIDTH / 2, HEIGHT / 2 - 50, lambda: self.change_scene("game")),
                   MenuOption("Ship Editor", WIDTH / 2, HEIGHT / 2,
                              lambda: self.change_scene("ship_editor")),
                   MenuOption("Options", WIDTH / 2, HEIGHT / 2 + 50,
                              lambda: self.change_scene("options")),
                   MenuOption("Exit", WIDTH / 2, HEIGHT / 2 + 100, lambda: self.root.quit())])
    elif scene == "game":
      for i in range(100):
        objs.append(CircleCreator())

  def preupdate(self):
    mouse['cursor'] = 'arrow'

  def postupdate(self):
    renderer.label.config(cursor=mouse['cursor'])


gameManager = GameManager(root)

# Init, draw, main


def init():
  #

  root.title("|| Birds in Space ||")
  root.geometry(f"{WIDTH}x{HEIGHT}")
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
  gameManager.postupdate()

  # Draw game state
  renderer.clearScreen()
  for obj in objs:
    obj.draw()

  # Print debug (FPS)
  if delta > 0:
    renderer.text(10, 10, f"FPS: {1 / delta:.2f}", "white")

  # Update the Tkinter image
  renderer.refreshTkinterImage()

  # Draw next frame in 33 ms
  root.after(33, mainloop)


if __name__ == '__main__':
  init()
  mainloop()
  root.mainloop()
