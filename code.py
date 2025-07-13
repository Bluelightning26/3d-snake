import board
import neopixel
import time
import random
import digitalio
# Two separate NeoPixel strips
pixels_panels_1_4 = neopixel.NeoPixel(board.GP0, 256, auto_write=False)  # Panels 1-4
pixels_panel_5 = neopixel.NeoPixel(board.GP3, 64, auto_write=False)      # Panel 5
pixels_panels_1_4.brightness = 0.05
pixels_panel_5.brightness = 0.05
PANEL_SIZE = 64
WIDTH = 8
HEIGHT = 8
PANEL_OFFSET = [0, 64, 128, 192]  # Only panels 1-4 now
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
    “”"Convert 3D coordinates to pixel index”“”
    if z == 5:  # Panel 5 is separate and needs flipping
        # Flip both horizontally and vertically for panel 5
        flipped_x = x  # Keep x as is
        flipped_y = y  # Keep y as is
        return flipped_y * 8 + flipped_x
    else:  # Panels 1-4
        base = PANEL_OFFSET[z - 1]
        return base + (7 - y) * 8 + (7 - x)
def set_pixel(x, y, z, color):
    “”"Set a pixel on the appropriate strip”“”
    index = coord_to_index(x, y, z)
    if z == 5:
        if 0 <= index < 64:
            pixels_panel_5[index] = color
    else:
        if 0 <= index < 256:
            pixels_panels_1_4[index] = color
def wrap_position(x, y, z, dx, dy, dz):
    “”"Wrap position based on exact cube topology schematic”“”
    nx, ny, nz = x + dx, y + dy, z + dz
    # If within bounds, no wrapping needed
    if 0 <= nx < 8 and 0 <= ny < 8 and 1 <= nz <= 5:
        return (nx, ny, nz), (dx, dy, dz)
    # Handle wrapping based on which edge we’re crossing
    # LEFT EDGE WRAPPING (x becomes -1)
    if nx == -1:
        if z == 1:  # Panel 1 left → Panel 2 right
            return (7, y, 2), (dx, dy, dz)
        elif z == 2:  # Panel 2 left → Panel 3 right
            return (7, y, 3), (dx, dy, dz)
        elif z == 3:  # Panel 3 left → Panel 4 right
            return (7, y, 4), (dx, dy, dz)
        elif z == 4:  # Panel 4 left → Panel 1 right
            return (7, y, 1), (dx, dy, dz)
        elif z == 5:  # Panel 5 left → Panel 4 top (moving down from Panel 4's perspective)
            return (y, 0, 4), (0, 1, 0)  # Direction becomes “down” on Panel 4
    # RIGHT EDGE WRAPPING (x becomes 8)
    elif nx == 8:
        if z == 1:  # Panel 1 right → Panel 4 left
            return (0, y, 4), (dx, dy, dz)
        elif z == 2:  # Panel 2 right → Panel 1 left
            return (0, y, 1), (dx, dy, dz)
        elif z == 3:  # Panel 3 right → Panel 2 left
            return (0, y, 2), (dx, dy, dz)
        elif z == 4:  # Panel 4 right → Panel 3 left
            return (0, y, 3), (dx, dy, dz)
        elif z == 5:  # Panel 5 right → Panel 2 top (moving down from Panel 2's perspective)
            return (7 - y, 0, 2), (0, 1, 0)  # Direction becomes “down” on Panel 2
    # TOP EDGE WRAPPING (y becomes -1, remember y=0 is TOP)
    elif ny == -1:
        if z == 1:  # Panel 1 top → Panel 5 bottom
            return (7 - x, 0, 5), (0, 1, 0)  # Moving up on Panel 5
        elif z == 2:  # Panel 2 top → Panel 5 right
            return (7, 7 - x, 5), (-1, 0, 0)  # Moving left on Panel 5
        elif z == 3:  # Panel 3 top → Panel 5 top
            return (x, 7, 5), (0, -1, 0)  # Moving down on Panel 5
        elif z == 4:  # Panel 4 top → Panel 5 left
            return (0, x, 5), (1, 0, 0)  # Moving right on Panel 5
        elif z == 5:  # Panel 5 top → Panel 3 top (moving down from Panel 3's perspective)
            return (7-x, 0, 1), (0, 1, 0)  # Direction becomes “down” on Panel 3
    # BOTTOM EDGE WRAPPING (y becomes 8)
    elif ny == 8:
        if z == 5:  # Panel 5 bottom → Panel 1 top (moving down from Panel 1's perspective)
            return (x, 0, 3), (0, 1, 0)  # Direction becomes “down” on Panel 1
        else:
            # Bottom edges of panels 1-4 don’t wrap anywhere
            return None, None
    return None, None
def read_joystick():
    global last_x, last_y, direction
    x = JOYSTICK_X.value
    y = JOYSTICK_Y.value
    # Handle X-axis changes (left/right)
    if x != last_x and last_x is not None:
        if not x:  # X button pressed (True to False transition)
            direction = turn_left(direction)
        last_x = x
    # Handle Y-axis changes (up/down) - separate from X-axis
    if y != last_y and last_y is not None:
        if not y:  # Y button pressed (True to False transition)
            direction = turn_up(direction)
        else:  # Y button released (False to True transition)
            direction = turn_down(direction)
        last_y = y
    # Initialize on first run
    if last_x is None:
        last_x = x
    if last_y is None:
        last_y = y
def turn_left(current_dir):
    dx, dy, dz = current_dir
    if dx == 1 and dy == 0:
        return (0, -1, 0)
    elif dx == -1 and dy == 0:
        return (0, 1, 0)
    elif dx == 0 and dy == 1:
        return (1, 0, 0)
    elif dx == 0 and dy == -1:
        return (-1, 0, 0)
    return current_dir
def turn_right(current_dir):
    dx, dy, dz = current_dir
    if dx == 1 and dy == 0:
        return (0, 1, 0)
    elif dx == -1 and dy == 0:
        return (0, -1, 0)
    elif dx == 0 and dy == 1:
        return (-1, 0, 0)
    elif dx == 0 and dy == -1:
        return (1, 0, 0)
    return current_dir
def turn_up(current_dir):
    dx, dy, dz = current_dir
    if dz == 0:
        return (0, -1, 0)
    return current_dir
def turn_down(current_dir):
    dx, dy, dz = current_dir
    if dz == 0:
        return (0, 1, 0)
    return current_dir
def draw():
    # Clear all pixels with dim green background
    for i in range(256):
        pixels_panels_1_4[i] = (0, 30, 0)
    for i in range(64):
        pixels_panel_5[i] = (0, 30, 0)
    # Draw snake in blue
    for x, y, z in snake:
        set_pixel(x, y, z, (0, 0, 255))
    # Draw apple in red
    ax, ay, az = apple
    set_pixel(ax, ay, az, (255, 0, 0))
    # Show both strips
    pixels_panels_1_4.show()
    pixels_panel_5.show()
def move():
    global snake, apple, direction
    read_joystick()
    head = snake[-1]
    new_pos, new_dir = wrap_position(*head, *direction)
    # Check for collision or invalid move
    if new_pos is None or new_pos in snake:
        # Reset game
        snake = [(4, 4, 1)]
        direction = (1, 0, 0)
        apple = (random.randint(0, 7), random.randint(0, 7), random.randint(1, 5))
        return
    # Update direction if it changed due to wrapping
    if new_dir != direction:
        direction = new_dir
    snake.append(new_pos)
    # Check if apple was eaten
    if new_pos == apple:
        # Generate new apple position
        while True:
            apple = (random.randint(0, 7), random.randint(0, 7), random.randint(1, 5))
            if apple not in snake:
                break
    else:
        # Remove tail if no apple eaten
        snake.pop(0)
def game_loop():
    while True:
        move()
        draw()
        time.sleep(0.2)
game_loop()
