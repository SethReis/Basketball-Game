# Basketball-Game
Code for an arcade pop-a-shot style game, made over the course of winter break 2022.

# How To Run:
Running this project will require the use of a Raspberry Pi flashed with Rasbian OS. Start by extracting the "BasketballProject" folder to the Raspberry Pi's user directory, likely labeled "/home/pi/". Then, clone the RGB LED Matrix Control repository (cited below), also into "/home/pi/". Finally, once the Raspberry Pi is wired, change the GPIO pins in "BasketballProject/basketballCode.py" as well as in "rpi-rgb-led-matrix/lib/hardware-mapping.c" to suit your needs, run the proper makefiles in rpi-rgb-led-matrix (follow their instructions on that Github page), and run basketballCode.py using sudo.

# Documentation Notes:

I use "canvas", "scoreboard", and "RGB matrix" interchangably in the code commenting, as they are all the same thing.
"Clock" and "timer" are used interchangably as well.

# Known Issues:
The first pair of scrolling text is misaligned the first time it runs, but all other scrolling text is aligned afterwards:
This is because the centering offset is only applied when the text is changed, but not the first time the text is initially set. The centering process uses the distance covered by the drawn text, but when assigning the positions of the first pair of scrolling text, it has not been drawn yet because drawing the text requires the positions to already be set. There are workarounds I know of to fix this, but it is a minor issue that causes no errors.

The RGB LED matrix has a slight flickering issue:
From my research, this appears to occur because the Raspberry Pi is running too fast for the RGB LED matrix to handle, since something relatively high tech is being used for a comparably simple purpose. The rate at which data is sent out to the RGB LED matrix can be slowed down, but it cannot be made perfect while still using the Raspberry Pi.

The backboard LEDs and timer sometimes flash once every second, for a few seconds:
This appears to be a wiring issue, since it only started occuring once the backboard LEDs and timer electronics were moved onto the backboard piece, while the code remained unchanged. I believe the wires could have been damaged slighly due to the backboard piece sitting on top of them for a prolonged amount of time at some point.

The timer glitches for a split second whenever a point is scored, and then reverts back to normal:
I believe this is due to power being drawn when a point is scored in order to change the backboard LEDs, since the backboard LEDs and timer likely run off the same power wire.

# Citations:
Sparkfun Starter Code for Our Model of Seven Segment Display: https://learn.sparkfun.com/tutorials/large-digit-driver-hookup-guide

Translation of Sparkfun Starter Code from Arduino to Python by Jonah Lefkoff: https://medium.com/@jonah.lefkoff/how-to-hook-up-the-sparkfun-7-segment-display-to-a-raspberry-pi-577591ba94b5

RGB LED Matrix Control Library for Raspberry Pi by Henner Zeller: https://github.com/hzeller/rpi-rgb-led-matrix
