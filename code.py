import board
import neopixel
import time
import random
import analogio

# === Joystick sensitivity settings ===
JOYSTICK_THRESHOLD = 20  # How far from center to count as a movement (0–100)
JOYSTICK_LEEWAY = 15     # How much to allow from the non-dominant axis

# Two separate NeoPixel strips
pixels_panels_1_4 = neopixel.NeoPixel(board.GP0, 256, auto_write=False)  # Panels 1-4
pixels_panel_5 = neopixel.NeoPixel(board.GP3, 64, auto_write=False)      # Panel 5

pixels_panels_1_4.brightness = 0.10
pixels_panel_5.brightness = 0.10

PANEL_SIZE = 64
WIDTH = 8
HEIGHT = 8
PANEL_OFFSET = [0, 64, 128, 192]  # Only panels 1-4 now

# Use analog inputs for joystick axes
JOYSTICK_X = analogio.AnalogIn(board.GP26)
JOYSTICK_Y = analogio.AnalogIn(board.GP27)

# Joystick center analog values
CENTER_X = 51196
CENTER_Y = 48571

# Max analog value for scaling (16-bit ADC max)
MAX_ANALOG = 65535

snake = [(4, 4, 1)]
direction = (1, 0, 0)
apple = (random.randint(0, 7), random.randint(0, 7), random.randint(1, 5))

def coord_to_index(x, y, z):
    if z == 5:
        return y * 8 + x
    else:
        base = PANEL_OFFSET[z - 1]
        return base + (7 - y) * 8 + (7 - x)

def set_pixel(x, y, z, color):
    index = coord_to_index(x, y, z)
    if z == 5:
        if 0 <= index < 64:
            pixels_panel_5[index] = color
    else:
        if 0 <= index < 256:
            pixels_panels_1_4[index] = color

def wrap_position(x, y, z, dx, dy, dz):
    nx, ny, nz = x + dx, y + dy, z + dz
    if 0 <= nx < 8 and 0 <= ny < 8 and 1 <= nz <= 5:
        return (nx, ny, nz), (dx, dy, dz)

    if nx == -1:
        if z == 1: return (7, y, 2), (dx, dy, dz)
        elif z == 2: return (7, y, 3), (dx, dy, dz)
        elif z == 3: return (7, y, 4), (dx, dy, dz)
        elif z == 4: return (7, y, 1), (dx, dy, dz)
        elif z == 5: return (y, 0, 4), (0, 1, 0)

    elif nx == 8:
        if z == 1: return (0, y, 4), (dx, dy, dz)
        elif z == 2: return (0, y, 1), (dx, dy, dz)
        elif z == 3: return (0, y, 2), (dx, dy, dz)
        elif z == 4: return (0, y, 3), (dx, dy, dz)
        elif z == 5: return (7 - y, 0, 2), (0, 1, 0)

    elif ny == -1:
        if z == 1: return (7 - x, 0, 5), (0, 1, 0)
        elif z == 2: return (7, 7 - x, 5), (-1, 0, 0)
        elif z == 3: return (x, 7, 5), (0, -1, 0)
        elif z == 4: return (0, x, 5), (1, 0, 0)
        elif z == 5: return (7 - x, 0, 1), (0, 1, 0)

    elif ny == 8:
        if z == 5: return (x, 0, 3), (0, 1, 0)
        else: return None

    return None

def read_joystick_analog():
    global direction
    raw_x = JOYSTICK_X.value
    raw_y = JOYSTICK_Y.value

    diff_x = raw_x - CENTER_X
    diff_y = raw_y - CENTER_Y

    scaled_x = int(diff_x * 100 / (MAX_ANALOG // 2))
    scaled_y = int(diff_y * 100 / (MAX_ANALOG // 2))

    print(f"Joystick analog position: X={raw_x}, Y={raw_y} | Scaled from center: X={scaled_x}%, Y={scaled_y}%")

    if abs(scaled_x) > JOYSTICK_THRESHOLD and abs(scaled_y) <= abs(scaled_x) + JOYSTICK_LEEWAY:
        direction = (1, 0, 0) if scaled_x > 0 else (-1, 0, 0)
    elif abs(scaled_y) > JOYSTICK_THRESHOLD and abs(scaled_x) <= abs(scaled_y) + JOYSTICK_LEEWAY:
        direction = (0, 1, 0) if scaled_y > 0 else (0, -1, 0)

def draw():
    for i in range(256):
        pixels_panels_1_4[i] = (0, 30, 0)
    for i in range(64):
        pixels_panel_5[i] = (0, 30, 0)
    for x, y, z in snake:
        set_pixel(x, y, z, (0, 0, 255))
    ax, ay, az = apple
    set_pixel(ax, ay, az, (255, 0, 0))
    pixels_panels_1_4.show()
    pixels_panel_5.show()

def move():
    global snake, apple, direction

    read_joystick_analog()

    head = snake[-1]
    result = wrap_position(*head, *direction)
    if result is None:
        snake[:] = [(4, 4, 1)]
        direction = (1, 0, 0)
        apple = (random.randint(0, 7), random.randint(0, 7), random.randint(1, 5))
        return

    new_pos, new_dir = result
    if new_pos is None or new_pos in snake:
        snake[:] = [(4, 4, 1)]
        direction = (1, 0, 0)
        apple = (random.randint(0, 7), random.randint(0, 7), random.randint(1, 5))
        return

    if new_dir != direction:
        direction = new_dir

    snake.append(new_pos)
    if new_pos == apple:
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
        time.sleep(0.1)

game_loop()

