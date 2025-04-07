from PIL import Image, ImageDraw, ImageTk
import tkinter as tk
import math


class Renderer:
  def __init__(self, root, window):
    self.window = window
    self.image = Image.new("RGB", (window['width'], window['height']),
                           "black")  # Create a blank image
    self.draw = ImageDraw.Draw(self.image)  # Drawing context
    self.tk_image = ImageTk.PhotoImage(self.image)  # Tkinter image
    self.label = tk.Label(root, image=self.tk_image, bg='#111', border=0)

    self.camX = 0
    self.camY = 0
    self.camHt = 1
    self.camGotoHt = 0.04
    self.hw = window['width'] / 2
    self.hh = window['height'] / 2

  def on_window_resize(self, event):
    self.window['width'] = w = event.width
    self.window['height'] = h = event.height
    self.hw = w / 2
    self.hh = h / 2
    self.image = Image.new("RGB", (w, h), "black")
    self.draw = ImageDraw.Draw(self.image)
    self.tk_image = ImageTk.PhotoImage(self.image)
    self.label.config(image=self.tk_image)
    self.cullX1 = 0
    self.cullY1 = 0
    self.cullX2 = w
    self.cullY2 = h

  def update(self, mouse, keys):
    # Update culling area
    self.cullX1 = self.RevX(0) - 2
    self.cullY1 = self.RevY(0) - 1
    self.cullX2 = self.RevX(self.window['width']) + 1
    self.cullY2 = self.RevY(self.window['height']) + 1

    # Smoothly transition to the target height
    self.camHt += (self.camGotoHt - self.camHt) * 0.5

    if mouse['scroll'] < 0:
      self.camGotoHt *= 1.2
      mouse['scroll'] = 0  # Reset scroll to prevent continuous zooming
    if mouse['scroll'] > 0:
      self.camGotoHt *= 0.8
      mouse['scroll'] = 0  # Reset scroll to prevent continuous zooming

  def levelEditorControls(self, mouse, keys):
    # WASD controls for camera movement, scroll wheel for zooming
    if keys.get('w', False):
      self.camY -= 0.1 * self.camHt * self.hw
    if keys.get('s', False):
      self.camY += 0.1 * self.camHt * self.hw
    if keys.get('a', False):
      self.camX -= 0.1 * self.camHt * self.hw
    if keys.get('d', False):
      self.camX += 0.1 * self.camHt * self.hw
    if keys.get('Up', False):
      self.camGotoHt *= 0.9
    if keys.get('Down', False):
      self.camGotoHt *= 1.1

  def load_image(self, path):
    try:
      img = Image.open(f'imgs/{path}')
      img = img.convert("RGBA")  # Convert to RGBA for transparency support
      return img
    except Exception as e:
      print(f"Error loading image: {e}")
      return None

  def clearScreen(self):
    self.image.paste(
      "black", [0, 0, self.window['width'], self.window['height']])

  def refreshTkinterImage(self):
    self.tk_image.paste(self.image)  # Update the Tkinter image

  def rect(self, x, y, w, h, color):
    self.draw.rectangle([x, y, w, h], color)

  def rect_outlined(self, x, y, w, h, color, outline):
    self.draw.rectangle([x, y, w, h], fill=color, outline=outline)

  def circle(self, x, y, r, color):
    self.draw.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=color)

  def line(self, x1, y1, x2, y2, color, width):
    self.draw.line([x1, y1, x2, y2], fill=color, width=math.ceil(width))

  def text(self, x, y, text, color):
    self.draw.text((x, y), text, fill=color)

  def text_center(self, x, y, text, color):
    self.draw.text((x, y), text, fill=color, align="center", anchor="mm")

  def img(self, img, x, y, size):
    print(f"img: {img}, x: {x}, y: {y}, size: {size}")
    w, h = img.size
    h = h * size / w
    img = img.resize((math.ceil(size), math.ceil(h)), Image.Resampling.LANCZOS)
    self.image.paste(img, (int(x - w / 2), int(y - h / 2)), img)

  # Convert world X coordinate to screen X position
  def X(self, x):
    return self.hw + (x - self.camX) / self.camHt

  def Y(self, y):
    return self.hh + (y - self.camY) / self.camHt

  def S(self, s):
    return s / self.camHt

  def RevX(self, x):
    return (x - self.hw) * self.camHt + self.camX

  def RevY(self, y):
    return (y - self.hh) * self.camHt + self.camY

  def RevS(self, s):
    return s * self.camHt

  def world_circle(self, x, y, r, color):
    self.circle(self.X(x), self.Y(y), self.S(r), color)

  def world_img(self, img, x, y, size):
    if x < self.cullX1 or x > self.cullX2 or y < self.cullY1 or y > self.cullY2:
      return
    w, h = img.size
    h = h * size / w
    img = img.resize((math.ceil(self.S(size)), math.ceil(self.S(h))),
                     Image.Resampling.LANCZOS)
    self.image.paste(img, (int(self.X(x)),
                     int(self.Y(y))), img)

  def world_img_flipped(self, img, x, y, size):
    if x < self.cullX1 or x > self.cullX2 or y < self.cullY1 or y > self.cullY2:
      return
    w, h = img.size
    h = h * size / w
    img = img.transpose(Image.FLIP_LEFT_RIGHT).resize((math.ceil(self.S(size)), math.ceil(self.S(h))),
                                                      Image.Resampling.LANCZOS)
    self.image.paste(img, (int(self.X(x)),
                     int(self.Y(y))), img)

  def world_img_rot(self, img, x, y, size, rotation):
    img = img.resize((math.ceil(self.S(size)), math.ceil(self.S(size / 2))),
                     Image.Resampling.LANCZOS)
    img = img.rotate(-rotation * 180 / math.pi, expand=True)
    sr = math.sin(rotation)
    cr = math.cos(rotation)
    ox = 0
    oy = 0
    if sr > 0:
      if cr > 0:
        ox = - sr * size / 2
      else:
        ox = cr * size - sr * size / 2
        oy = cr * size / 2
    else:
      if cr > 0:
        oy = sr * size
      else:
        ox = cr * size
        oy = +cr * size/2 + sr * size
        # oy = sr * size / 2 - 1 -           cr * size / 2
        # - math.sin(rotation * 2) * size / 4
    # if ox < 0:
    #   ox = -ox
    self.image.paste(img, (math.ceil(self.X(x + ox)),
                     math.ceil(self.Y(y + oy))), img)

  def world_polygon(self, points, color):
    # Convert world coordinates to screen coordinates
    screen_points = [(self.X(x), self.Y(y)) for x, y in points]
    self.draw.polygon(screen_points, fill=color, outline=color)

  def world_line(self, x1, y1, x2, y2, color, width):
    self.line(self.X(x1), self.Y(y1), self.X(x2), self.Y(y2), color, self.S(width))

  def world_rect(self, x, y, w, h, color):
    self.rect(self.X(x), self.Y(y), self.X(x + w), self.Y(y + h), color)
