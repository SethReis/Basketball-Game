#!/usr/bin/env python

import RPi.GPIO as GPIO
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import math
import threading
from PIL import ImageFont
import pygame
from pygame import mixer
import time
from time import sleep


def config():
  configGPIO()
  configMixer()
  configScoreboard()
  configHighScore()
  configIdle()
  configPlayBall()

def configGPIO():
  # Start of GPIO declarations and initializations
  GPIO.setmode(GPIO.BCM)
  
  # Seven Segment Display GPIO
  global segmentData, segmentLatch, segmentClock
  segmentData = 8
  segmentLatch = 10
  segmentClock = 11

  GPIO.setup(segmentData, GPIO.OUT, initial = 0)
  GPIO.setup(segmentLatch, GPIO.OUT, initial = 0)
  GPIO.setup(segmentClock, GPIO.OUT, initial = 0)

  # Backboard LEDs GPIO
  global backboardB, backboardR, backboardG
  backboardB = 5
  backboardR = 12
  backboardG = 13

  GPIO.setup(backboardG, GPIO.OUT, initial = 1)
  GPIO.setup(backboardR, GPIO.OUT, initial = 1)
  GPIO.setup(backboardB, GPIO.OUT, initial = 1)

  # Input Devices GPIO
  global threePointer, resetBtn, ballSensor, startBtn
  threePointer = 6
  resetBtn = 9
  ballSensor = 16
  startBtn = 27

  GPIO.setup(threePointer, GPIO.IN, GPIO.PUD_DOWN)
  GPIO.setup(resetBtn, GPIO.IN)
  GPIO.setup(ballSensor, GPIO.IN, GPIO.PUD_DOWN)
  GPIO.setup(startBtn, GPIO.IN)
  # End of GPIO declarations and initializations

  # Add specific event types to sensors for specialized situations
  GPIO.add_event_detect(resetBtn, GPIO.FALLING)
  GPIO.add_event_detect(ballSensor, GPIO.RISING)
  GPIO.add_event_detect(startBtn, GPIO.FALLING)

def configMixer():
  # Initialize sound mixer and load sounds
  mixer.init()
  global overThirtySound, underThirtySound, newHighScoreSound, playIdleSounds
  overThirtySound = mixer.Sound("/home/pi/BasketballProject/NotBad.wav")
  underThirtySound = mixer.Sound("/home/pi/BasketballProject/MorePractice.wav")
  newHighScoreSound = mixer.Sound("/home/pi/BasketballProject/HighScore.wav")
  playIdleSounds = True

def configScoreboard():
  # Set RGB matrix parameters and initialize to variable
  global options
  options = RGBMatrixOptions()
  options.rows = 32
  options.cols = 64
  options.chain_length = 1
  options.parallel = 1
  options.gpio_slowdown = 2
  options.hardware_mapping = 'regular'

  global scoreboard
  scoreboard = RGBMatrix(options = options)

  # Create canvas variables
  global offscreen_canvas
  offscreen_canvas = scoreboard.CreateFrameCanvas()

  global font, textColor
  font = graphics.Font()
  textColor = graphics.Color(255, 0, 0)

def configHighScore():
  # Open and get text from file used to save high score
  global highScoreFile, highScore
  highScoreFile = open("/home/pi/BasketballProject/highScore.txt", "r+")
  highScoreFile.seek(0)
  highScore = highScoreFile.readline()
  if (not highScore.isdigit()):
    highScore = 0
  else:
    highScore = int(highScore)

def configIdle():
  # Initialize idle starting conditions
  global text_to_scroll_top, text_to_scroll_bottom, current_text, wait_to_scroll
  text_to_scroll_top = ["TEST YOUR", "HI SCORE:", "PUSH TO", "REIS\u2122"]
  text_to_scroll_bottom = ["MIGHT", "", "START", "2022"]
  current_text = 0
  wait_to_scroll = 0

  global my_text_top, my_text_bottom, pos_top, pos_bottom
  my_text_top = text_to_scroll_top[current_text]
  my_text_bottom = text_to_scroll_bottom[current_text]
  pos_top = offscreen_canvas.width
  pos_bottom = offscreen_canvas.width

def configPlayBall():
  # Initialize playBall starting conditions
  global scoring, score, lastBasketScored, ledCount, threePointerTimeCheck, lastBallSensorRes
  scoring = False
  score = 0
  lastBasketScored = 0
  ledCount = 0
  threePointerTimeCheck = [0 for i in range(5)]
  lastBallSensorRes = False

def main():
  global gameState
  gameState = idle

  global inputsThread
  inputsThread = threading.Thread(target = respondToInputs, name = "Input Responder", args =[])
  inputsThread.start()

  font.LoadFont("/home/pi/rpi-fb-matrix/rpi-rgb-led-matrix/fonts/6x13.bdf")

  while True:
    if (gameState == playBall):
      playBall()
    else:
      idle()

def cleanup():
  # Cleanup for if the code ever reaches here
  highScoreFile.close()
  GPIO.cleanup()


def respondToInputs():
  global scoring, score, lastBasketScored, ledCount, lastBallSensorRes
  global playIdleSounds, lastResetBtnRes, highScore, highScoreFile
  global gameState

  while True:
    if (gameState == playBall):
      # If a rising change is detected on the IR shot sensor AND the sensor value is above the voltage threshold AND we are reading a new ball
      if GPIO.event_detected(ballSensor):
        if (GPIO.input(ballSensor) == True) and (lastBallSensorRes == True):
          if (scoring == False):
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
              
            sleep(0.4)
            
        else:
          # Otherwise, if the sensor value is below the voltage threshold, then we are not reading a ball right now
          scoring = False
      
      lastBallSensorRes = GPIO.input(ballSensor)
    
    # Else, if we're idling
    else:
      # If the start button is pressed in (its wired backwards, which is why it checks for False, not True)
      if GPIO.event_detected(startBtn):
        if (GPIO.input(startBtn) == False):
          gameState = playBall
          
#      # If the reset button is being pressed in
#      if GPIO.event_detected(resetBtn):
#        if (GPIO.input(resetBtn) == False):
#          # Wait 3 seconds
#          sleep(3)
#          # And if the reset button is still being pressed
#          if (GPIO.input(resetBtn) == False):
#            # Then clear the high score and reset it to 0
#            highScoreFile.seek(0)
#            highScoreFile.truncate()
#            highScoreFile.write("0")
#            highScoreFile.close()
#            configHighScore()
#          else:
#            # Otherwise (reset button pressed for less than 3 seconds), enable/disable the idle sounds
#            playIdleSounds = not playIdleSounds
#            mixer.music.stop()
#            
#          sleep(2)
      

def idle():
  global offscreen_canvas
  global text_to_scroll_bottom, current_text, wait_to_scroll
  global my_text_top, my_text_bottom, pos_top, pos_bottom
  global dist_top, dist_bottom

  # Body of code where multiline text is scrolled while a game is not being played
  # Clear canvas and draw text (not rendered yet)
  offscreen_canvas.Clear()
  dist_top = graphics.DrawText(offscreen_canvas, font, pos_top, 15, textColor, my_text_top)
  dist_bottom = graphics.DrawText(offscreen_canvas, font, pos_bottom, 27, textColor, my_text_bottom)

  # If the text should not be paused in the middle of the screen, move it
  if (wait_to_scroll == 0):
    pos_top -= 1
    pos_bottom -= 1
    
  # If the text just moved into the middle, stop it for ~1.5 seconds
  if (pos_top + (dist_top/2) == 32 and wait_to_scroll == 0):
    wait_to_scroll = 45
  elif (pos_top + dist_top < 0 and pos_bottom + dist_bottom < 0):
    # Else, if both the top line and bottom line of text are completely off the canvas to the left
    # Change to the next set of text to scroll, or loop back around to the first set of text
    current_text += 1
    if (current_text >= len(text_to_scroll_bottom)):
      current_text = 0
    
    # If the text to scroll should display the high score, update whatever high score it is set to display
    if (current_text == 1):
      text_to_scroll_bottom[current_text] = str(highScore)
    
    # Save text to scroll and reposition it off the canvas to the right
    my_text_top = text_to_scroll_top[current_text]
    my_text_bottom = text_to_scroll_bottom[current_text]
    
    dist_top = graphics.DrawText(offscreen_canvas, font, pos_top, 15, textColor, my_text_top)
    dist_bottom = graphics.DrawText(offscreen_canvas, font, pos_bottom, 27, textColor, my_text_bottom)
    offscreen_canvas.Clear()

    pos_top = offscreen_canvas.width
    pos_bottom = offscreen_canvas.width + math.ceil((dist_top)/2) - math.floor((dist_bottom)/2)
    
  # Render canvas
  offscreen_canvas = scoreboard.SwapOnVSync(offscreen_canvas)

  # If the text is paused in the middle of the screen, decrease how much longer its paused for
  if (wait_to_scroll > 0):
    wait_to_scroll -= 1

  # Wait a tiny bit
  sleep(0.033)

  if (playIdleSounds) and (not mixer.music.get_busy()):
    mixer.music.load("/home/pi/BasketballProject/52secondfinal.mp3")
    mixer.music.play(-1)


# Code for the basketball game itself
def playBall():
  global offscreen_canvas, ledCount, gameState, highScore, highScoreFile

  font.LoadFont("/home/pi/rpi-fb-matrix/rpi-rgb-led-matrix/fonts/texgyre-27.bdf")
  offscreen_canvas.Clear()
  offscreen_canvas = scoreboard.SwapOnVSync(offscreen_canvas)

  # Load and play game music
  mixer.music.load("/home/pi/BasketballProject/52secondfinal.mp3")
  mixer.music.play()

  # Initialize other local variables
  ledToggle = True

  # 3, 2, 1 Countdown until game starts
  clearClock()
  sleep(3)

  for i in range(3, 0, -1):
    showNumber(i)
    sleep(1)

  sleep(0.333)

  configPlayBall()
  
  #Game starts, set scoreboard to be "000" and always as three digits
  my_text = str(score)
  my_text = my_text.zfill(3)
  offscreen_canvas.Clear()
  graphics.DrawText(offscreen_canvas, font, 9, 26, textColor, my_text)
  offscreen_canvas = scoreboard.SwapOnVSync(offscreen_canvas)
  
  for i in range(459, 9, -1):
    # Check and save current time before running game code
    start_time = time.time()

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
    sleep(0.095 - (time.time() - start_time))

  # The game has finished, make backboard lights red until we finish
  GPIO.output(backboardB, False)
  GPIO.output(backboardG, False)
  showNumber(0)
  sleep(3)
  
  # Determine which voice line to play based on if the player got a new high score, got over 30, or got under 30
  # Also, wait until the voice line finishes to move on
  if (score > highScore):
    chan = newHighScoreSound.play()
    while chan.get_busy():
      sleep(0)
      #wait till sound stops
  elif (score >= 30):
    chan = overThirtySound.play()
    while chan.get_busy():
      sleep(0)
      #wait till sound stops
  else:
    chan = underThirtySound.play()
    while chan.get_busy():
      sleep(0)
      #wait till sound stops
  
  # Set backboard lights to white, stop the music, clear the scoreboard, and saves highScore or score, whichever is higher
  sleep(1)
  GPIO.output(backboardB, True)
  GPIO.output(backboardG, True)
  clearClock()
  offscreen_canvas.Clear()
  offscreen_canvas = scoreboard.SwapOnVSync(offscreen_canvas)
  mixer.music.stop()
  
  # Overwrite old high score with new high score
  newScore = score if score > highScore else highScore
  highScoreFile.seek(0)
  highScoreFile.truncate()
  highScoreFile.write(str(newScore))
  highScoreFile.close()
  configHighScore()

  # Config back to idle
  font.LoadFont("/home/pi/rpi-fb-matrix/rpi-rgb-led-matrix/fonts/6x13.bdf")
  configIdle()
  gameState = idle


# Clears the game clock (Seven Segment Display)
# Doing this as the game runs mitigates flickering on the seven segment display when power is drawn due to changing the backboard LEDs
def clearClock():
  for j in range(16):
    GPIO.output(segmentClock, GPIO.LOW)
    GPIO.output(segmentData, GPIO.LOW)
    GPIO.output(segmentClock, GPIO.HIGH)

  GPIO.output(segmentLatch, GPIO.LOW)
  GPIO.output(segmentLatch, GPIO.HIGH)


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


config()
main()
cleanup()