# line spacing messed up by Slack

import board
import neopixel
import time
import random
import digitalio
pixels = neopixel.NeoPixel(board.GP0, 320, auto_write=False)
pixels.brightness = 0.05
PANEL_SIZE = 64
WIDTH = 8
HEIGHT = 8
PANEL_OFFSET = [0, 64, 128, 192, 256]
JOYSTICK_X = digitalio.DigitalInOut(board.GP26)
JOYSTICK_X.direction = digitalio.Direction.INPUT
JOYSTICK_X.pull = digitalio.Pull.UP
JOYSTICK_Y = digitalio.DigitalInOut(board.GP27)
JOYSTICK_Y.direction = digitalio.Direction.INPUT
JOYSTICK_Y.pull = digitalio.Pull.UP
snake = [(4, 4, 1)]
direction = (1, 0, 0)
apple = (random.randint(0, 7), random.randint(0, 7), random.randint(1, 5))
last_x = None
last_y = None
def coord_to_index(x, y, z):
    base = PANEL_OFFSET[z - 1]
    return base + (7 - y) * 8 + (7 - x)
def read_joystick():
    global last_x, last_y, direction
    x = JOYSTICK_X.value
    y = JOYSTICK_Y.value
    if x != last_x and last_x is not None:
        last_x = x
        if not x:
            direction = (-1, 0, 0)
        else:
            direction = (1, 0, 0)
    elif y != last_y and last_y is not None:
        last_y = y
        if not y:
            direction = (0, -1, 0)
        else:
            direction = (0, 1, 0)
    if last_x is None:
        last_x = x
    if last_y is None:
        last_y = y
def wrap_position(x, y, z, dx, dy, dz):
    nx, ny, nz = x + dx, y + dy, z + dz
    if 0 <= nx < 8 and 0 <= ny < 8 and 1 <= nz <= 5:
        return (nx, ny, nz)
    if z == 1:
        if dx == -1 and x == 0:
            return (7, y, 2)
        elif dx == 1 and x == 7:
            return (0, y, 4)
        elif dy == 1 and y == 7:
            return (x, 0, 5)
        elif dy == -1 and y == 0:
            return None
    elif z == 2:
        if dx == -1 and x == 0:
            return (7, y, 3)
        elif dx == 1 and x == 7:
            return (0, y, 1)
        elif dy == 1 and y == 7:
            return (0, x, 5)
        elif dy == -1 and y == 0:
            return None
    elif z == 3:
        if dx == -1 and x == 0:
            return (7, y, 4)
        elif dx == 1 and x == 7:
            return (0, y, 2)
        elif dy == 1 and y == 7:
            return (7 - x, 7, 5)
        elif dy == -1 and y == 0:
            return None
    elif z == 4:
        if dx == -1 and x == 0:
            return (7, y, 1)
        elif dx == 1 and x == 7:
            return (0, y, 3)
        elif dy == 1 and y == 7:
            return (7, x, 5)
        elif dy == -1 and y == 0:
            return None
    elif z == 5:
        if dx == -1 and x == 0:
            return (0, y, 2)
        elif dx == 1 and x == 7:
            return (7, y, 4)
        elif dy == -1 and y == 0:
            return (x, 7, 1)
        elif dy == 1 and y == 7:
            return (7 - x, 7, 3)
    return (nx, ny, nz) if 0 <= nx < 8 and 0 <= ny < 8 and 1 <= nz <= 5 else None
def draw():
    for i in range(320):
        pixels[i] = (0, 30, 0)
    for x, y, z in snake:
        pixels[coord_to_index(x, y, z)] = (0, 0, 255)
    ax, ay, az = apple
    pixels[coord_to_index(ax, ay, az)] = (255, 0, 0)
    pixels.show()
def move():
    global snake, apple, direction
    read_joystick()
    head = snake[-1]
    wrapped = wrap_position(*head, *direction)
    if not wrapped or wrapped in snake:
        snake = [(0, 0, 1)]
        direction = (1, 0, 0)
        apple = (random.randint(0, 7), random.randint(0, 7), random.randint(1, 5))
        return
    snake.append(wrapped)
    if wrapped == apple:
        while True:
            apple = (random.randint(0, 7), random.randint(0, 7), random.randint(1, 5))
            if apple not in snake:
                break
    else:
        snake.pop(0)
def game_loop():
    while True:
        move()
        draw()
        time.sleep(0.2)
game_loop()
