import time
import board
import pwmio
import tm1637
import digitalio

# === Volume control ===
inputVolume = 10  # in percent
volume = inputVolume / 100

# === Display setup ===
display1 = tm1637.TM1637(clk=board.GP22, dio=board.GP28)
display1.brightness(0)

display2 = tm1637.TM1637(clk=board.GP20, dio=board.GP21)
display2.brightness(0)

# === Buzzer setup on GP15 ===
buzzer = pwmio.PWMOut(board.GP15, duty_cycle=0, frequency=440, variable_frequency=True)

def play_note(freq):
    global volume
    buzzer.frequency = int(freq)
    buzzer.duty_cycle = int(65530 * volume)

def stop_note():
    buzzer.duty_cycle = 0

# === Button setup on GP17 ===
button = digitalio.DigitalInOut(board.GP17)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# === Melody sequence ===
melody = [
    130.81, 0, 130.81, 0, 196, 0, 196, 0, 220, 0, 220, 0, 196, 0,
    174.61, 0, 174.61, 0, 164.81, 0, 164.81, 0, 146.83, 0, 146.83, 0, 130.81, 0,
    196, 0, 196, 0, 174.61, 0, 174.61, 0, 164.81, 0, 164.81, 0, 146.83, 0,
    196, 0, 196, 0, 174.61, 0, 174.61, 0, 164.81, 0, 164.81, 0, 146.83, 0,
    130.81, 0, 130.81, 0, 196, 0, 196, 0, 220, 0, 220, 0, 196, 0,
    174.61, 0, 174.61, 0, 164.81, 0, 164.81, 0, 146.83, 0, 146.83, 0,
    130.81, 130.81, 130.81, 0
]

melody_index = 0
note_start_time = time.monotonic()
note_duration = 0.1  # seconds

# === Counter state ===
counter1 = 0
counter2 = 0
last_update = time.monotonic()

# === Main loop ===
while True:
    now = time.monotonic()

    # Reset counters if button is pressed
    if not button.value:
        counter1 = 0
        counter2 = 0
        display1.show("0000")
        display2.show("0000")
        time.sleep(0.2)  # Debounce delay

    # Update counters every 0.1s
    if now - last_update >= 0.1:
        counter1 += 1
        counter2 += 1

        if counter1 > 9999:
            counter1 = 0
        if counter2 > 9999:
            counter2 = 0

        display1.show(f"{counter1:04d}")
        display2.show(f"{counter2:04d}")

        last_update = now

    # Play melody one note at a time
    if melody_index < len(melody):
        if now - note_start_time >= note_duration:
            freq = melody[melody_index]
            if freq == 0:
                stop_note()
            else:
                play_note(freq)
            melody_index += 1
            note_start_time = now
    else:
        melody_index = 0  # Loop the song

    time.sleep(0.005)


