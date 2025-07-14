

import board
import neopixel
import time
import random
import analogio
import pwmio
import tm1637
import digitalio
import digitalio
import time

# === Motor Control Setup ===
# GPIO pin assignments for DRV8825
DIR_PIN = board.GP2    # Direction control
STEP_PIN = board.GP8   # Step control
SLP_PIN = board.GP4    # Sleep control (active HIGH)
RST_PIN = board.GP5    # Reset control (active HIGH)
FLT_PIN = board.GP6    # Fault pin (optional, active LOW when fault)
EN_PIN = board.GP7     # Enable control (active LOW)

# Initialize motor control pins
dir_pin = digitalio.DigitalInOut(DIR_PIN)
dir_pin.direction = digitalio.Direction.OUTPUT

step_pin = digitalio.DigitalInOut(STEP_PIN)
step_pin.direction = digitalio.Direction.OUTPUT

sleep_pin = digitalio.DigitalInOut(SLP_PIN)
sleep_pin.direction = digitalio.Direction.OUTPUT

reset_pin = digitalio.DigitalInOut(RST_PIN)
reset_pin.direction = digitalio.Direction.OUTPUT

enable_pin = digitalio.DigitalInOut(EN_PIN)
enable_pin.direction = digitalio.Direction.OUTPUT

# Optional fault pin (input with pull-up)
fault_pin = digitalio.DigitalInOut(FLT_PIN)
fault_pin.direction = digitalio.Direction.INPUT
fault_pin.pull = digitalio.Pull.UP

# Motor configuration
STEPS_PER_90_DEGREES = 50  # 90° rotation
MAX_ROTATION_STEPS = 200   # 360° limit (4 * 50 steps)

# Motor state tracking
current_rotation_steps = 0  # Track total rotation from start position
target_panel = 1  # Current target panel


def init_motor():
    """Initialize the DRV8825 driver"""
    print("Initializing DRV8825 driver...")
    
    # Enable driver (active LOW)
    enable_pin.value = False
    
    # Enable driver (wake up from sleep)
    sleep_pin.value = True
    
    # Release reset (active high)
    reset_pin.value = True
    
    # Set initial direction
    dir_pin.value = True  # True = CW, False = CCW
    step_pin.value = False
    
    time.sleep(0.1)  # Allow driver to initialize
    print("Driver initialized!")

def check_motor_fault():
    """Check if there's a fault condition"""
    return not fault_pin.value  # Fault is active LOW


def step_motor(steps=50, direction=True, delay=0.001):
    """
    Step the motor
    steps: number of steps to take
    direction: True for clockwise, False for counter-clockwise
    delay: delay between steps in seconds
    """
    if check_fault():
        print("ERROR: Fault detected! Check wiring and power supply.")
        return
    
    dir_pin.value = direction
    print(f"Stepping {steps} steps {'CW' if direction else 'CCW'}")
    
    for i in range(steps):
        step_pin.value = True
        time.sleep(delay)
        step_pin.value = False
        time.sleep(delay)
        
        # Check fault every 100 steps
        if i % 100 == 0 and check_fault():
            print(f"Fault detected at step {i}!")
            break

def move_motor(clockwise=True, delay=0.001):
    """
    Move motor exactly 90 degrees (50 steps)
    Based on the step_motor function from tester code
    Returns True if successful, False if failed
    """
    global current_rotation_steps
    
    if check_motor_fault():
        print("ERROR: Fault detected! Check wiring and power supply.")
        return False
    
    # Set direction
    dir_pin.value = clockwise
    print(f"Stepping {STEPS_PER_90_DEGREES} steps {'CW' if clockwise else 'CCW'}")
    
    # Step the motor using the same pattern as tester code
    for i in range(STEPS_PER_90_DEGREES):
        step_pin.value = True
        time.sleep(delay)
        step_pin.value = False
        time.sleep(delay)
        
        # Check fault every 10 steps (more frequent than tester's 100)
        if i % 10 == 0 and check_motor_fault():
            print(f"Fault detected at step {i}!")
            return False
    
    # Update current position
    if clockwise:
        current_rotation_steps += STEPS_PER_90_DEGREES
    else:
        current_rotation_steps -= STEPS_PER_90_DEGREES
    
    print(f"Motor moved successfully. Current position: {current_rotation_steps} steps")
    return True

def calculate_rotation_to_panel(current_panel, target_panel):
    """
    Calculate how many 90° rotations needed to get from current to target panel
    Returns (number_of_rotations, clockwise_direction)
    Positive rotations = clockwise, negative = counter-clockwise
    """
    # Panel arrangement: 1(front) -> 2(right) -> 3(back) -> 4(left) -> 1...
    diff = target_panel - current_panel
    
    # Normalize to shortest path
    if diff > 2:
        diff -= 4  # Go CCW instead
    elif diff < -2:
        diff += 4  # Go CW instead
    
    return diff  # Positive = CW, negative = CCW

def rotate_to_panel(target_panel_num):
    """
    Rotate cube to show specified panel on the left
    Handles 360° limit by choosing alternative direction if needed
    """
    global target_panel, current_rotation_steps
    
    if target_panel_num == target_panel:
        return True  # Already at target
    
    # Calculate ideal rotation
    rotations_needed = calculate_rotation_to_panel(target_panel, target_panel_num)
    
    # Check if ideal rotation would exceed limits
    projected_steps = current_rotation_steps + (rotations_needed * STEPS_PER_90_DEGREES)
    
    if abs(projected_steps) > MAX_ROTATION_STEPS:
        # Try opposite direction (non-ideal but within limits)
        print(f"Ideal rotation would exceed 360° limit, trying opposite direction")
        rotations_needed = -rotations_needed
        if rotations_needed > 0:
            rotations_needed = 4 - rotations_needed  # Go the long way around
        else:
            rotations_needed = -4 - rotations_needed  # Go the long way around
        
        projected_steps = current_rotation_steps + (rotations_needed * STEPS_PER_90_DEGREES)
        
        if abs(projected_steps) > MAX_ROTATION_STEPS:
            print(f"Cannot rotate to panel {target_panel_num}: would exceed limits in both directions")
            return False
    
    # Perform the rotation
    clockwise = rotations_needed > 0
    abs_rotations = abs(rotations_needed)
    
    print(f"Rotating {abs_rotations} steps to reach panel {target_panel_num}")
    
    for i in range(abs_rotations):
        if not move_motor(clockwise):
            print(f"Motor movement failed at rotation {i+1}")
            return False
        time.sleep(0.05)  # Small delay between 90° rotations
    
    target_panel = target_panel_num
    print(f"Successfully rotated to panel {target_panel}")
    return True


def update_cube_rotation():
    """
    Update cube rotation based on snake head position
    Call this function in your main game loop
    """
    if not snake:  # Safety check
        return
    
    # Get snake head position
    head_x, head_y, head_z = snake[-1]
    
    # Only rotate for lateral panels (1-4)
    if head_z in [1, 2, 3, 4]:
        # We want the snake's panel to be on the left
        if head_z != target_panel:
            print(f"Snake moved to panel {head_z}, rotating cube...")
            if not rotate_to_panel(head_z):
                print("Failed to rotate to optimal view")

def reset_cube_rotation():
    """
    Reset cube to original position (panel 1 on left)
    Call this when game resets
    """
    global target_panel, current_rotation_steps
    
    if current_rotation_steps == 0:
        return  # Already at start position
    
    print("Resetting cube to original position...")
    
    # Calculate how many 90° rotations to get back to start
    rotations_to_zero = -current_rotation_steps // STEPS_PER_90_DEGREES
    
    if rotations_to_zero != 0:
        clockwise = rotations_to_zero > 0
        abs_rotations = abs(rotations_to_zero)
        
        for i in range(abs_rotations):
            if not move_motor(clockwise):
                print(f"Reset failed at rotation {i+1}")
                return False
            time.sleep(0.05)
    
    target_panel = 1
    current_rotation_steps = 0
    print("Cube reset to original position")
    return True





# initialize score displys 

# display1 = high score display
display1 = tm1637.TM1637(clk=board.GP22, dio=board.GP28)
display1.brightness(0)


# display2 = current score display
display2 = tm1637.TM1637(clk=board.GP20, dio=board.GP21)
display2.brightness(0)


# initializes motor; ADD THIS TO YOUR INITIALIZATION SECTION (after display setup):
init_motor()



high_score = 0
current_score = 0

display1.show(f"{high_score:04d}")
display2.show(f"{current_score:04d}")










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

    update_cube_rotation()

def show_score():
	global current_score, high_score
	current_score = len(snake) - 1  # Score is the length of the snake minus the initial segment
	display2.show(f"{current_score:04d}")
	
	if current_score > high_score:
		high_score = current_score
		display1.show(f"{high_score:04d}")

def game_loop():
    while True:
        move()
        draw()
        show_score()
        time.sleep(0.15)

        if check_motor_fault():
            print("Motor fault detected in game loop!")
        

if(current_score > high_score):
	high_score = current_score
	display1.show(f"{high_score:04d}")

game_loop()


