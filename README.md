# Basketball-Game
Code for an arcade pop-a-shot style basketball game on Raspberry Pi, made over the course of winter break 2022.

# How To Run:
Running this project will require the use of a Raspberry Pi (I used a Raspberry Pi 3 B+) and an SD card of large enough size (32GB should be more than enough). I've made the process of installing this software on a new SD card easy by including a disk image in the zip file above. Simply download [Raspberry Pi Imager](https://www.raspberrypi.com/software/), select the above disk image as a custom OS installation, and finish the process. You should be left with a copy of the project on your SD card ready to insert into your Raspberry Pi.

Alternatively, if you wish to add this project to an existing OS installation (only tested with Rasbian OS), one can do so by SSHing into the Raspberry Pi remotely when the SD card is inserted, which is how I worked on this project without a monitor directly connect. Find out how to set up a Raspberry Pi without a monitor [here](https://www.tomshardware.com/reviews/raspberry-pi-headless-setup-how-to,6028.html#:~:text=Write%20an%20empty%20text%20file,command%20line%20from%20your%20PC.). I personally used [MobaXTerm](https://mobaxterm.mobatek.net/) to SSH in, as it allows for drag-and-drop file transfer between the local and remote system. After SSHing into the Raspberry Pi, drag the "BasketballProject" folder to the Raspberry Pi's user directory, likely labeled "/home/pi/". Then, clone the RGB LED Matrix Control repository (cited below) also into "/home/pi/". 

No matter which option you choose from the above, after your Raspberry Pi is wired, the GPIO pins in "BasketballProject/basketballCode.py" as well as in "rpi-rgb-led-matrix/lib/hardware-mapping.c" can changed to suit your needs. The RGB LED matrix was directly wired to the Raspberry Pi in my case, but you may use something like the Adafruit RGB Matrix Hat or Bonnet, in which case that option should be selected in rpi-rgb-led-matrix/lib/Makefile. Again, more specific instruction on how to use the RGB LED Matrix Control library are on its github page below (I did not code it, I am just reporting my understanding of it). Then, run the proper makefiles in rpi-rgb-led-matrix (follow their instructions) and run basketballCode.py using sudo.

# Documentation Notes:

I use "canvas", "scoreboard", and "RGB matrix" interchangably in the code commenting, as they are all the same thing.

"Clock" and "timer" are used interchangably as well.

# Known Issues:
### The first pair of scrolling text is misaligned the first time it runs, but all other scrolling text is aligned afterwards: ###
This is because the centering offset is only applied when the text is changed, but not the first time the text is initially set. The centering process uses the distance covered by the drawn text, but when assigning the positions of the first pair of scrolling text, it has not been drawn yet because drawing the text requires the positions to already be set. There are workarounds I know of to fix this, but it is a minor issue that causes no errors.

### The RGB LED matrix has a slight flickering issue: ###
From my research, this is partly because the Raspberry Pi is running too fast for the RGB LED matrix to handle, since something relatively high tech is being used for a comparably simple purpose. The GPIO output to the RGB LED matrix can be slowed down to mitigate this, and has been done in the code provided. My other recommendation is to make sure all of the files are correctly made in the rpi-rgb-led-matrix/ directory. When using Python, there may be as many as three seperate makefiles that must be ran to guarentee changes to hardware-mapping.c are carried over to the program.

### All lights sometimes flash once every second, for a few seconds: ###
This appears to be a wiring issue, since it only started occuring once the backboard LEDs and timer electronics were moved onto the backboard piece, while the code remained unchanged. There may be some crossing of wires, since the flashing occurs even when code is not running.

### The timer glitches for a split second whenever a point is scored, and then reverts back to normal: ###
I believe this is due to power being drawn when a point is scored in order to change the backboard LEDs, since the backboard LEDs and timer likely run off the same power wire.

# Citations:
Sparkfun Starter Code for Our Model of Seven Segment Display: https://learn.sparkfun.com/tutorials/large-digit-driver-hookup-guide

Translation of Sparkfun Starter Code from Arduino to Python by Jonah Lefkoff: https://medium.com/@jonah.lefkoff/how-to-hook-up-the-sparkfun-7-segment-display-to-a-raspberry-pi-577591ba94b5

RGB LED Matrix Control Library for Raspberry Pi by Henner Zeller: https://github.com/hzeller/rpi-rgb-led-matrix
