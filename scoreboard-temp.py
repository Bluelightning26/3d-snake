import time
import board
import tm1637


# Display 1: GP26 (CLK), GP27 (DIO)
display1 = tm1637.TM1637(board.GP26, board.GP27)
display1.brightness(0)

# Display 2: GP20 (CLK), GP21 (DIO)
display2 = tm1637.TM1637(board.GP20, board.GP21)
display2.brightness(3)

counter1 = 0
counter2 = 0
last_update = time.monotonic()

while True:
    now = time.monotonic()

    # Update both displays every 0.1s
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

    time.sleep(0.01)


