#!/usr/bin/env python

import RPi.GPIO as GPIO
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import math
from PIL import ImageFont
import pygame
from pygame import mixer
import time
from time import sleep

# Start of GPIO declarations and initializations
GPIO.setmode(GPIO.BCM)

segmentData = 8
segmentLatch = 10
segmentClock = 11

backboardB = 5
backboardR = 12
backboardG = 13

threePointer = 6
resetBtn = 9
ballSensor = 16
startBtn = 27

GPIO.setup(segmentData, GPIO.OUT, initial = 0)
GPIO.setup(segmentLatch, GPIO.OUT, initial = 0)
GPIO.setup(segmentClock, GPIO.OUT, initial = 0)

GPIO.setup(backboardG, GPIO.OUT, initial = 1)
GPIO.setup(backboardR, GPIO.OUT, initial = 1)
GPIO.setup(backboardB, GPIO.OUT, initial = 1)

GPIO.setup(threePointer, GPIO.IN, GPIO.PUD_DOWN)
GPIO.setup(resetBtn, GPIO.IN)
GPIO.setup(ballSensor, GPIO.IN)
GPIO.setup(startBtn, GPIO.IN)
# End of GPIO declarations and initializations

# Add specific event types to sensors for specialized situations
GPIO.add_event_detect(resetBtn, GPIO.FALLING)
GPIO.add_event_detect(ballSensor, GPIO.RISING)
GPIO.add_event_detect(startBtn, GPIO.FALLING)

# Initialize sound mixer and load sounds
mixer.init()
overFiftySound = mixer.Sound("/home/pi/BasketballProject/NotBad.wav")
underFiftySound = mixer.Sound("/home/pi/BasketballProject/MorePractice.wav")
newHighScoreSound = mixer.Sound("/home/pi/BasketballProject/HighScore.wav")

# Open text file used to save high score
highScoreFile = open("/home/pi/BasketballProject/highScore.txt", "r+")

# Set RGB matrix parameters and initialize to variable
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.gpio_slowdown = 2
options.hardware_mapping = 'regular'
scoreboard = RGBMatrix(options = options)

# Create canvas variables and initialize starting conditions
offscreen_canvas = scoreboard.CreateFrameCanvas()
font = graphics.Font()
font.LoadFont("/home/pi/rpi-fb-matrix/rpi-rgb-led-matrix/fonts/6x13.bdf")
textColor = graphics.Color(255, 0, 0)
text_to_scroll_top = ["TEST YOUR", "HI SCORE:", "PUSH TO", "REIS\u2122"]
text_to_scroll_bottom = ["MIGHT", "", "START", "2022"]
current_text = 0
wait_to_scroll = 0
my_text_top = text_to_scroll_top[current_text]
my_text_bottom = text_to_scroll_bottom[current_text]
pos_top = offscreen_canvas.width
pos_bottom = offscreen_canvas.width


# Code for the basketball game itself, including scorekeeping, shot registering, and canvas rendering
# Input: highScore, the previous high score before the current game began
# Output: highScore or score (obtained during game), whichever is higher
def playBall(highScore):
  # Load initial scoreboard conditions
  offscreen_canvas = scoreboard.CreateFrameCanvas()
  font.LoadFont("/home/pi/rpi-fb-matrix/rpi-rgb-led-matrix/fonts/texgyre-27.bdf")
  offscreen_canvas.Clear()
  offscreen_canvas = scoreboard.SwapOnVSync(offscreen_canvas)

  # Load and play game music
  mixer.music.load("/home/pi/BasketballProject/52secondfinal.mp3")
  mixer.music.play()

  # Initialize other local variables
  ledCount = 0
  lastBasketScored = 0
  ledToggle = True
  threePointerTimeCheck = [0 for i in range(5)]

  score = 0
  scoring = False
  
  # 3, 2, 1 Countdown until game starts
  clearClock()
  sleep(3)

  for i in range(3, 0, -1):
    showNumber(i)
    sleep(1)

  sleep(0.333)
  
  #Game starts, set scoreboard to be "000" and always as three digits
  my_text = str(score)
  my_text = my_text.zfill(3)
  offscreen_canvas.Clear()
  graphics.DrawText(offscreen_canvas, font, 9, 26, textColor, my_text)
  offscreen_canvas = scoreboard.SwapOnVSync(offscreen_canvas)
  
  for i in range(459, 9, -1):
    # Check and save current time before running game code
    start_time = time.time()
    
    # If a rising change is detected on the IR shot sensor AND the sensor value is above the voltage threshold AND we are reading a new ball
    if GPIO.event_detected(ballSensor):
      if GPIO.input(ballSensor) == True:
        if scoring == False:
          # Then remember that we are reading a ball for later use, and increase the score
          scoring = True
          score += 2
          lastBasketScored = 2
          ledCount = 5
          # If someone has been on the three pointer pressure pad for at least 0.5 seconds
          if (GPIO.input(threePointer) == True) and (threePointerTimeCheck[0] == 1):
            # Then register the show as a three pointer instead, and change variables accordingly
            score += 1
            lastBasketScored = 3
            ledCount = 10
      else:
        # Otherwise, if the sensor value is below the voltage threshold, then we are not reading a ball right now
        scoring = False

    # Append currrent three-pointer pressure sensor status to list, and remove oldest value (from 0.5 seconds ago)
    threePointerTimeCheck.append(GPIO.input(threePointer))
    threePointerTimeCheck.pop(0)

    # Update score variable and scoreboard
    my_text = str(score)
    my_text = my_text.zfill(3)
    offscreen_canvas.Clear()
    graphics.DrawText(offscreen_canvas, font, 9, 26, textColor, my_text)
    offscreen_canvas = scoreboard.SwapOnVSync(offscreen_canvas)

    # Determine how the backboard LEDs should behave, based on what the last basket scored was and how long ago it was scored
    # This section of code also update the game timer on the seven segment display
    if (ledCount != 0):
      if (lastBasketScored == 2):
        # Backboard LEDs are solid green after a two-pointer
        GPIO.output(backboardB, False)
        GPIO.output(backboardR, False)
        ledCount -= 1
      else:
        # Or flash between green and white after a three-pointer
        GPIO.output(backboardB, not ledToggle)
        GPIO.output(backboardR, not ledToggle)
        ledToggle = not ledToggle
        ledCount -= 1

      showNumber(i/10)
    else:
      GPIO.output(backboardB, True)
      GPIO.output(backboardR, True)
      ledToggle = False
      showNumber(i/10)

    # Wait for 0.1 seconds minus however long it took to run the above code in the for loop, such that we always wait 0.1 seconds total
    # This is done so the game timer stays accurate and syncs up with the music in the background
    sleep(0.1 - (time.time() - start_time))

  # The game has finished, make backboard lights red until we return
  GPIO.output(backboardB, False)
  GPIO.output(backboardG, False)
  showNumber(0)
  sleep(3)
  
  # Determine which voice line to play based on if the player got a new high score, got over 50, or got under 50
  # Also, wait until the voice line finishes to move on
  if score > highScore:
    chan = newHighScoreSound.play()
    while chan.get_busy():
      sleep(0)
      #wait till sound stops
  elif (score >= 50):
    chan = overFiftySound.play()
    while chan.get_busy():
      sleep(0)
      #wait till sound stops
  else:
    chan = underFiftySound.play()
    while chan.get_busy():
      sleep(0)
      #wait till sound stops
  
  # Set backboard lights to white, stop the music, clear the scoreboard, and return highScore or score, whichever is higher
  sleep(1)
  GPIO.output(backboardB, True)
  GPIO.output(backboardG, True)
  clearClock()
  offscreen_canvas.Clear()
  offscreen_canvas = scoreboard.SwapOnVSync(offscreen_canvas)
  mixer.music.stop()
  
  return score if score > highScore else highScore



# START OF SPARKFUN CODE TRANSLATED BY JONAH LEFKOFF

#Takes a number and displays 2 numbers. Display absolute value (no negatives)
#look here maybe bug between value+number
def showNumber(value):
  number = abs(value) #Remove negative signs and any decimals
  x=0
  while(x<2):
    remainder= math.floor(number) % 10
    postNumber(remainder)
    number /= 10
    x += 1
#Latch the current segment data
  GPIO.output(segmentLatch,GPIO.LOW)
  GPIO.output(segmentLatch,GPIO.HIGH) #Register moves storage register on the rising edge of RCK
#Given a number, or - shifts it out to the display
def postNumber(number):
  a=1<<0
  b=1<<6
  c=1<<5
  d=1<<4
  e=1<<3
  f=1<<1
  g=1<<2
  dp=1<<7
  if   number == 1: segments =     b | c
  elif number == 2: segments = a | b |     d | e |     g
  elif number == 3: segments = a | b | c | d |         g
  elif number == 4: segments =     b | c |         f | g
  elif number == 5: segments = a |     c | d     | f | g
  elif number == 6: segments = a |     c | d | e | f | g
  elif number == 7: segments = a | b | c
  elif number == 8: segments = a | b | c | d | e | f | g
  elif number == 9: segments = a | b | c | d     | f | g
  elif number == 0: segments = a | b | c | d | e | f
  elif number == ' ': segments = 0
  elif number == 'c': segments = g | e | d
  elif number == '-': segments = g
  else : segments = False
#if (segments != dp):
  y=0
  while(y<8):
    GPIO.output(segmentClock,GPIO.LOW)
    GPIO.output(segmentData,segments & 1 << (7-y))
    GPIO.output(segmentClock,GPIO.HIGH)
    y += 1

# END OF SPARKFUN CODE TRANSLATED BY JONAH LEFKOFF



# Clears the game clock (Seven Segment Display)
# Doing this as the game runs mitigates flickering on the seven segment display when power is drawn due to changing the backboard LEDs
def clearClock():
  for j in range(16):
    GPIO.output(segmentClock, GPIO.LOW)
    GPIO.output(segmentData, GPIO.LOW)
    GPIO.output(segmentClock, GPIO.HIGH)

  GPIO.output(segmentLatch, GPIO.LOW)
  GPIO.output(segmentLatch, GPIO.HIGH)


# Main body of code, where multiline text is scrolled while a game is not being played
while True:
  # Clear canvas and draw text (not rendered yet)
  offscreen_canvas.Clear()
  dist_top = graphics.DrawText(offscreen_canvas, font, pos_top, 15, textColor, my_text_top)
  dist_bottom = graphics.DrawText(offscreen_canvas, font, pos_bottom, 27, textColor, my_text_bottom)
  
  # Checks if the scrolling text should currently be paused in the middle of the screen, and responds accordingly
  if (wait_to_scroll == 0):
    pos_top -= 1
    pos_bottom -= 1
  else:
    wait_to_scroll -= 1
    if (wait_to_scroll == 0):
      pos_top -= 1
      pos_bottom -= 1
  
  # If the text just moved into the middle, stop it for ~1.5 seconds
  if (pos_top + (dist_top/2) == 32 and wait_to_scroll == 0):
    wait_to_scroll = 45
  elif (pos_top + dist_top < 0 and pos_bottom + dist_bottom < 0):
    # Else, if both the top line and bottom line of text are completely off the canvas to the left
    # Change to the text set of text to scroll, or loop back around to the first set of text
    current_text += 1
    if (current_text >= len(text_to_scroll_bottom)):
      current_text = 0
    
    # If the text to scroll should display the high score, update whatever high score it is set to display
    if (current_text == 1):
      highScoreFile.seek(0)
      text_to_scroll_bottom[current_text] = highScoreFile.readline()
    
    # Save text to scroll, draw text, and reposition it off the canvas to the right
    my_text_top = text_to_scroll_top[current_text]
    my_text_bottom = text_to_scroll_bottom[current_text]
    
    dist_top = graphics.DrawText(offscreen_canvas, font, pos_top, 15, textColor, my_text_top)
    dist_bottom = graphics.DrawText(offscreen_canvas, font, pos_bottom, 27, textColor, my_text_bottom)
    offscreen_canvas.Clear()
    
    pos_top = offscreen_canvas.width
    pos_bottom = offscreen_canvas.width + math.ceil((dist_top)/2) - math.floor((dist_bottom)/2)
    
  # Render canvas, and wait a tiny bit
  offscreen_canvas = scoreboard.SwapOnVSync(offscreen_canvas)
  sleep(0.033)
  
  # If the start button is pressed in (its wired backwards, which is why it checks for False, not True)
  if GPIO.event_detected(startBtn):
    # If the idle sounds were playing before the game started, play them after the game finishes, otherwise don't
    if (GPIO.input(startBtn) == False):
      replayIdleSounds = False
      if mixer.music.get_busy():
        replayIdleSounds = True
        mixer.music.stop()
      
      # Get current high score, and run the game while passing this in
      highScoreFile.seek(0)
      highScore = int(highScoreFile.readline())
      newScore = playBall(highScore)
      
      # Reload canvas settings that were changed while the game ran
      font.LoadFont("/home/pi/rpi-fb-matrix/rpi-rgb-led-matrix/fonts/6x13.bdf")
      
      # Overwrite old high score with new high score
      highScoreFile.seek(0)
      highScoreFile.truncate()
      highScoreFile.write(str(newScore))
      
      # Reset scrolling text conditions back to their initial values, instead of resuming where it left of before the game
      current_text = 0
      my_text_top = text_to_scroll_top[current_text]
      my_text_bottom = text_to_scroll_bottom[current_text]
      
      dist_top = graphics.DrawText(offscreen_canvas, font, pos_top, 15, textColor, my_text_top)
      dist_bottom = graphics.DrawText(offscreen_canvas, font, pos_bottom, 27, textColor, my_text_bottom)
      offscreen_canvas.Clear()
    
      pos_top = offscreen_canvas.width
      pos_bottom = offscreen_canvas.width + math.ceil((dist_top)/2) - math.floor((dist_bottom)/2)
      
      # Replay idle sounds if it should
      if replayIdleSounds:
        mixer.music.load("/home/pi/BasketballProject/52secondfinal.mp3")
        mixer.music.play(-1)
    
  # If the reset button is being pressed in (also wired backwards)
  if GPIO.event_detected(resetBtn):
    if GPIO.input(resetBtn) == False:
      sleep(3)
      # Wait three seconds, and if its still being pressed
      if GPIO.input(resetBtn) == False:
        # Then clear the high score and reset it to 0
        highScoreFile.seek(0)
        highScoreFile.truncate()
        highScoreFile.write("0")
      else:
        # Otherwise (reset button pressed for less than 3 seconds), enable/disable the idle sounds
        if mixer.music.get_busy():
          mixer.music.stop()
        else:
          mixer.music.load("/home/pi/BasketballProject/52secondfinal.mp3")
          mixer.music.play(-1)
        
      sleep(2)

# Cleanup for if the code ever reaches here
highScoreFile.close()
GPIO.cleanup()
