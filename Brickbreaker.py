from tkinter import *
import math
import random
import string
from image_util import *
import numpy as np
import pyaudio
import math
from math import sin, cos
import copy


################
# Beat Detection
################
song = None

FORMAT = pyaudio.paInt16 # We use 16bit format per sample
CHANNELS = 2
RATE = 44100
CHUNK = 1024

pa = pyaudio.PyAudio()

# start Recording
stream = pa.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

intensityAvg = 0
intensityList = []
listAvg = 0
beat = False
pause = 0
dfft = None

def updateVisualizer():
    global intensityAvg,intensityList, dfft, beat, listAvg, pause
    intensitySum=0
    song = stream.read(1024, exception_on_overflow = False)
    audioData = np.frombuffer(song, np.int16)
    dfft = np.fft.rfft(audioData)

    intensityAvg = sum(dfft) / len(dfft)
    intensityList.append(intensityAvg)
    if len(intensityList) > 43:
        intensityList.pop(0)

    listAvg = sum(intensityList) / len(intensityList)
    pause += 1
    x = 0
    #Constants from http://mziccard.me/2015/05/28/beats-detection-algorithms-1/
    for i in intensityList:
        diff = (i-intensityAvg)**2
        x += diff
    c = (-0.0000015*x)+ 1.15142857

    if abs(intensityAvg) > abs(c * listAvg):
        if pause <= 10: beat = False
        elif pause >= 10:
            pause = 0
            beat = True
        else: beat = False

#################################
# Brickbreaker Object Class Setup
#################################

from Object import *

#############################################
# Methods that involve Collision with objects
#############################################

def collideWithWall(data):
    #Left Wall and Right Wall
    if data.ball.x - data.ball.radius <= 0 or \
        data.ball.x + data.ball.radius > data.width:
        angleWithNormal = data.ball.angle - (math.pi * 2 / 4)
        data.ball.angle -= 2 * angleWithNormal
    #Top Wall
    elif data.ball.y - data.ball.radius < 0:
        angleWithNormal = data.ball.angle - (math.pi * 2 / 2)
        data.ball.angle -= 2 * angleWithNormal
    #Bellow Slider
    elif data.ball.y - data.ball.radius > data.topSlider + 50:
        data.lives -= 1
        data.start = True

#Changes direction of the ball based on where it hits the slider
def collideWithSlider(data):
    randList = [-1, -0.75, -0.5, 0.5, 0.75, 1]
    randIn = random.randint(0, len(randList) - 1)
    #Hit slider
    if data.ball.y + data.ball.radius > data.topSlider and \
    (data.leftSlider < data.ball.x < data.leftSlider + data.lengthSlider) and \
    data.ball.y < data.topSlider:
        posX = data.ball.x
        middleOfBoard = data.leftSlider + (data.lengthSlider // 2)
        posOnBoard = -(middleOfBoard - posX) // 5
        if posOnBoard == 0:
            posOnBoard = randList[randIn]
        data.ball.angle = ((posOnBoard/24) * ((math.pi * 2)/4)) - math.pi*2/4

def collideWithBrick(data, topX, topY):
    #Right
    if topX + 120 > data.ball.x - data.ball.radius > topX + 110 and \
            topY < data.ball.y < topY + 40:
        angleWithNormal = data.ball.angle - (math.pi * 2 / 4)
        data.ball.angle -= 2 * angleWithNormal
    #Left
    elif topX < data.ball.x + data.ball.radius < topX + 10 and \
            topY < data.ball.y < topY + 40:
        angleWithNormal = data.ball.angle - (math.pi * 2 / 4)
        data.ball.angle -= 2 * angleWithNormal
    #Top
    elif topY < data.ball.y + data.ball.radius < topY and \
            topX < data.ball.x < topX + 120:
        angleWithNormal = data.ball.angle - (math.pi * 2 / 2)
        data.ball.angle -= 2 * angleWithNormal
    #Bottom
    if topY < data.ball.y - data.ball.radius < topY + 40 and \
            topX < data.ball.x < topX + 120:
        angleWithNormal = data.ball.angle - (math.pi * 2 / 2)
        data.ball.angle -= 2 * angleWithNormal

##################################
# Methods that deal with power ups
##################################

#Method to test if a power up hit the slider
def powerHitSlider(data):
    counter = 0
    while counter < len(data.fallingPower):
        if data.fallingPower[counter].y + \
            data.fallingPower[counter].fallingHeight >= data.topSlider and \
            data.leftSlider <= data.fallingPower[counter].x <= \
            data.leftSlider + data.lengthSlider - \
            data.fallingPower[counter].fallingWidth:
            
            x = data.fallingPower.pop(counter)
            data.aquiredPower.append(x)
        else: counter += 1

#Method to go through all the current power ups ability
def aquiredPower(data, second):
    counter = 0
    while counter < len(data.aquiredPower): 
        if data.aquiredPower[counter].type == 1:
            if second == True:
                data.aquiredPower[counter].seconds -= 1
            if data.aquiredPower[counter].seconds > 0:
                data.lengthSlider = 190
                counter += 1
            else:
                data.lengthSlider = 150
                data.aquiredPower.pop(counter)
        elif data.aquiredPower[counter].type == 2:
            if second == True:
                data.aquiredPower[counter].seconds -= 1
            if data.aquiredPower[counter].seconds > 0:
                data.currentMutiply = data.aquiredPower[counter].mutiply
                counter += 1
            else:
                data.currentMutiply = 1
                data.aquiredPower.pop(counter)
        elif data.aquiredPower[counter].type == 3:
            data.start = True
            data.aquiredPower.pop(counter)
        elif data.aquiredPower[counter].type == 4: 
            data.lives += 1
            data.aquiredPower.pop(counter)

#################################################
# Used to generate a random level for arcade mode
#################################################

def randomLevelGenerator():
    two = [False, False, False, False, True, True, False, False, False, False]
    four = [False, False, False, True, True, True, True, False, False, False]
    six = [False, False, True, True, True, True, True, True, False, False]
    eight = [False, True, True, True, True, True, True, True, True, False]
    ten = [True, True, True, True, True, True, True, True, True, True]
    levelList = []
    for i in range(5):
        rLevel = random.choice([two, four, six, eight, ten])
        levelList.append(copy.copy(rLevel))
    for i in range(len(levelList)):
        for j in range(len(levelList[i])):
            if levelList[i][j] == True:
                if random.randint(1, 10) <= 2:
                    typ = random.randint(1, 4)
                    if typ == 1:
                        levelList[i][j] = WideSlider()
                    elif typ == 2:
                        levelList[i][j] = Multiplier()
                    elif typ == 3:
                        levelList[i][j] = Catch()
                    elif typ == 4:
                        levelList[i][j] = Life()
                else:
                    levelList[i][j] = Brick()
    return levelList

############
# Reset Data
############

def restart(data):
    data.isPaused = False
    data.lives = 3
    data.score = 0
    data.timeEllapsed = 0
    data.start = True
    data.aquiredPower = []
    data.fallingPower = []
    data.leftSlider = data.width // 2
    data.topSlider = data.height - 150
    data.lengthSlider = 150
    data.currentMutiply = 1


def init(data):
    data.arcadeMode = False
    data.isPaused = False
    data.gameOver = True
    data.endTime = 0
    data.endColor = "white"
    data.nameCounter = 0
    data.timeEllapsed = 0
    data.name = ""
    data.isSecond = False
    data.score = 0
    data.lives = 3
    data.aquiredPower = []
    data.fallingPower = []
    data.ball = Ball()
    data.start = True
    data.mode = "startScreen"
    data.leftSlider = data.width // 2
    data.topSlider = data.height - 150
    data.lengthSlider = 150
    data.currentMutiply = 1
    data.movement = 30

    data.startColorR = 250
    data.startColorG = 250
    data.startColorB = 250
    
    
    data.levelOne = [
                    [Brick(), Brick(), Multiplier(), Brick(), Catch(), Brick(), Brick(), Brick(), Life(), Catch()],
                    [False, Life(), Brick(), Brick(), Brick(), Brick(), Multiplier(), Brick(), Brick(), False], 
                    [False, False, Brick(), Multiplier(), Brick(), Brick(), Catch(), Brick(), False, False], 
                    [False, False, False, Brick(), Brick(), Brick(), Brick(), False, False, False],
                    [False, False, False, False, Brick(), WideSlider(), False, False, False, False],
                    ]
    
    data.levelTwo = [
                    [False, False, False, False, Brick(), Catch(), False, False, False, False],
                    [False, False, False, Catch(), Brick(), Brick(), Multiplier(), False, False, False], 
                    [False, False, Brick(), Brick(), Multiplier(), Multiplier(), Multiplier(), Brick(), False, False], 
                    [False, False, False, Brick(), WideSlider(), Brick(), Life(), False, False, False],
                    [False, False, False, False, Brick(), Multiplier(), False, False, False, False],
                    ]

    data.levelThree = [
                    [False, False, Brick(), Brick(), Brick(), Brick(), Brick(), Brick(), False, False],
                    [False, False, False, Brick(), Brick(), Life(), Brick(), False, False, False], 
                    [False, False, False, False, WideSlider(), Brick(), False, False, False, False], 
                    [False, False, False, Brick(), Brick(), Brick(), Brick(), False, False, False],
                    [False, False, Brick(), Multiplier(), Brick(), Brick(), Brick(), WideSlider(), False, False],
                    ]

    data.levelFour = [
                    [False, False, False, False, Brick(), Catch(), False, False, False, False],
                    [False, False, False, Brick(), Brick(), Brick(), Brick(), False, False, False],
                    [False, False, Brick(), WideSlider(), Life(), Brick(), Multiplier(), Brick(), False, False],
                    [False, Brick(), Brick(), Multiplier(), Brick(), Brick(), Brick(), Brick(), Brick(), False],
                    [Brick(), Multiplier(), Brick(), Brick(), Brick(), Brick(), Brick(), Multiplier(), Brick(), Brick()],     
                    ]


    data.levelFive = [
                    [False, False, Brick(), False, Brick(), Brick(), False, Brick(), False, False],
                    [False, Brick(), False, Brick(), False, False, Brick(), False, Brick(), False],
                    [Brick(), False, Brick(), False, Brick(), Brick(), False, Brick(), False, Brick()],
                    [False, Brick(), False, Brick(), False, False, Brick(), False, Brick(), False],
                    [False, False, Brick(), False, Brick(), Brick(), False, Brick(), False, False],
                    ]

    #Tester Levels
    """
    data.levelOne = [
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, Brick(), False, False, False, False, False],
                    ]
    
    data.levelTwo = [
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, Brick(), False, False, False, False, False],
                    ]
    data.levelThree = [
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, Brick(), False, False, False, False, False],
                    ]
    data.levelFour = [
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, Brick(), False, False, False, False, False],
                    ]
    data.levelFive = [
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, Brick(), False, False, False, False, False],
                    ]
    #"""

    data.fakeLevel = [[False]]

    data.levels = [data.levelOne, data.levelTwo, data.levelThree, \
                    data.levelFour, data.levelFive, data.fakeLevel]
    data.orgLevels = copy.deepcopy(data.levels) 

    #arcade level setup
    data.arcadeLevels = []
    for i in range(5):
        level = randomLevelGenerator()
        data.arcadeLevels.append(level)
    data.arcadeLevels.append(data.fakeLevel)
    data.orgAr = copy.deepcopy(data.arcadeLevels)
    data.currentLevel = 0

    #Brick image setup
    blue = PhotoImage(file="Sprites/blue.gif")
    cyan = PhotoImage(file="Sprites/cyan.gif")
    green = PhotoImage(file="Sprites/green.gif")
    lime = PhotoImage(file="Sprites/lime.gif")
    orange = PhotoImage(file="Sprites/orange.gif")
    purple = PhotoImage(file="Sprites/purple.gif")
    red = PhotoImage(file="Sprites/red.gif")
    yellow = PhotoImage(file="Sprites/yellow.gif")

    data.bricks = [blue, cyan, green, lime, orange, purple, red, yellow]
    data.heart = PhotoImage(file = "Sprites/heart.gif")
    data.heartWidth = data.heart.width()



###########################
# Different mode directions
###########################
def mousePressed(event, data):
    if data.mode == "playScreen": mousePressedPlay(event, data)
    elif data.mode == "endWinScreen": mousePressedWin(event, data)
    elif data.mode == "startScreen": mousePressedStart(event, data)
    elif data.mode == "helpScreen": mousePressedHelp(event, data)


def keyPressed(event, data):
    if data.mode == "playScreen": keyPressedPlay(event, data)
    elif data.mode == "endWinScreen": keyPressedWin(event, data)
    elif data.mode == "startScreen": keyPressedStart(event, data)
    elif data.mode == "helpScreen": keyPressedHelp(event, data)


def timerFired(data):
    if data.mode == "playScreen": timerFiredPlay(data)
    elif data.mode == "endWinScreen": timerFiredWin(data)
    elif data.mode == "startScreen": timerFiredStart(data)
    elif data.mode == "helpScreen": timerFiredHelp(data)

def redrawAll(canvas, data):
    if data.mode == "playScreen": redrawAllPlay(canvas, data)
    elif data.mode == "endWinScreen": redrawAllWin(canvas, data)
    elif data.mode == "startScreen": redrawAllStart(canvas, data)
    elif data.mode == "helpScreen": redrawAllHelp(canvas, data)


#########################
# Regular and Arcade Mode
#########################

def mousePressedPlay(evet, data):
    pass

def keyPressedPlay(event, data):
    #Pausing, quitting, and resuming
    if event.keysym == "Escape":
        data.isPaused = True
    elif event.keysym == "r":
        data.isPaused = False
    elif event.keysym == "q":
        data.mode = "startScreen"
        restart(data)
        if data.arcadeMode == False: data.levels = data.orgLevels
        else: data.arcadeLevels = data.orgAr

    #Slider movement plus space bar for start of round
    if data.isPaused == False:
        if(event.keysym == "space" and data.start == True):
            data.start = False
            data.ball.x = data.leftSlider + (data.lengthSlider / 2)
            data.ball.y = data.topSlider - data.ball.radius
        if (event.keysym == "Left" and data.leftSlider >= 0):
            data.leftSlider -= data.movement
        elif (event.keysym == "Right" and \
            data.leftSlider + data.lengthSlider <= data.width):
            data.leftSlider += data.movement

def timerFiredPlay(data):
    global beat, intensityAvg, listAvg
    updateVisualizer()
    if beat:
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        data.ball.color = [r,g,b]



    if data.isPaused == False:
        #Updates ball position
        data.ball.x += math.cos(data.ball.angle) * data.ball.speed
        data.ball.y += math.sin(data.ball.angle) * data.ball.speed

        #Checks if a second passed
        data.timeEllapsed += data.timerDelay
        if data.timeEllapsed % 500 == 0:
            data.isSecond = True
        else:
            data.isSecond = False
        #checks if the person lost
        if data.lives <= 0:
            data.fallingPower = []
            data.nameCounter = 0
            data.gameOver = True
            data.mode = "endWinScreen"

        #regular mode
        if data.arcadeMode == False:
            #In game
            if data.start == False and data.currentLevel < 5:
                numOfBricks = 0
                #Checks general collision
                collideWithWall(data)
                collideWithSlider(data)
                for i in range(len(data.levels[data.currentLevel])):
                    for j in range(len(data.levels[data.currentLevel][i])):
                        if data.levels[data.currentLevel][i][j] != False:
                            orgAng = data.ball.angle
                            numOfBricks += 1
                            #Chekcs collision with Brik
                            collideWithBrick(data, 
                                j*data.levels[data.currentLevel][i][j].width, 
                                i*data.levels[data.currentLevel][i][j].height)
                            #Collision happened
                            if orgAng != data.ball.angle:
                                #Checks if it is a special Power
                                if data.levels[data.currentLevel][i][j].type!=0:
                                    #Gives X and Y value of falling power up
                                    data.levels[data.currentLevel][i][j].x = \
                                    j*data.levels[data.currentLevel][i][j].width\
                                    + data.levels[data.currentLevel][i][j].width\
                                    // 2 - data.levels[data.currentLevel][i][j].fallingWidth // 2

                                    data.levels[data.currentLevel][i][j].y = \
                                    i*data.levels[data.currentLevel][i][j].height\
                                    + data.levels[data.currentLevel][i][j].height\
                                    // 2 - data.levels[data.currentLevel][i][j].fallingHeight // 2

                                    data.fallingPower.append(data.levels[data.currentLevel][i][j])
                                data.score += 10 * data.currentMutiply
                                data.levels[data.currentLevel][i][j] = False
                #0 if all the bricks in levels are gone
                if numOfBricks == 0:
                    data.currentLevel += 1
                    data.start = True
                    data.fallingPower = []

                #Updates power ups
                counter = 0
                while counter < len(data.fallingPower):
                    if data.fallingPower[counter].y + data.fallingPower[counter].speed >= data.height - 100:
                        data.fallingPower.pop(counter)
                    else: 
                        data.fallingPower[counter].y += data.fallingPower[counter].speed
                        counter += 1 
                powerHitSlider(data)
                aquiredPower(data, data.isSecond)
            #Catch
            elif data.start == True and data.currentLevel < 5:
                data.aquiredPower = []
                data.fallingPower = []
            #Won Game
            else:
                data.aquiredPower = []
                data.fallingPower = []
                data.nameCounter = 0
                data.gameOver = False
                data.mode = "endWinScreen"
        #If arcade is on (Similar to above code but uses a different list of levels)
        if data.arcadeMode == True:
            if data.start == False:
                numOfBricks = 0
                collideWithWall(data)
                collideWithSlider(data)
                for i in range(len(data.arcadeLevels[data.currentLevel])):
                    for j in range(len(data.arcadeLevels[data.currentLevel][i])):
                        if data.arcadeLevels[data.currentLevel][i][j] != False:
                            orgAng = data.ball.angle
                            numOfBricks += 1
                            collideWithBrick(data, 
                            j*data.arcadeLevels[data.currentLevel][i][j].width, 
                            i*data.arcadeLevels[data.currentLevel][i][j].height)
                            if orgAng != data.ball.angle:
                                if data.arcadeLevels[data.currentLevel][i][j].type != 0:
                                    data.arcadeLevels[data.currentLevel][i][j].x = \
                                    j*data.arcadeLevels[data.currentLevel][i][j].width + \
                                    data.arcadeLevels[data.currentLevel][i][j].width // 2 - \
                                    data.arcadeLevels[data.currentLevel][i][j].fallingWidth // 2

                                    data.arcadeLevels[data.currentLevel][i][j].y = \
                                    i*data.arcadeLevels[data.currentLevel][i][j].height + \
                                    data.arcadeLevels[data.currentLevel][i][j].height // 2  - \
                                    data.arcadeLevels[data.currentLevel][i][j].fallingHeight // 2
                                    data.fallingPower.append(data.arcadeLevels[data.currentLevel][i][j])
                                data.score += 10 * data.currentMutiply
                                data.arcadeLevels[data.currentLevel][i][j] = False
                if numOfBricks == 0:
                    data.currentLevel += 1
                    data.start = True
                    data.fallingPower = []
                counter = 0
                while counter < len(data.fallingPower):
                    if data.fallingPower[counter].y + data.fallingPower[counter].speed >= data.height - 80:
                        data.fallingPower.pop(counter)
                    else: 
                        data.fallingPower[counter].y += data.fallingPower[counter].speed
                powerHitSlider(data)
                aquiredPower(data, data.isSecond)
            elif data.start == True:
                data.aquiredPower = []
                data.fallingPower = []



#Redraws the Bottom part of the playing screen
def detailsRedraw(canvas, data):
    canvas.create_rectangle(0, data.height - 80, data.width, data.height, 
                            fill = "black")
    canvas.create_text(10, data.height - 40, anchor = "w", text = "Lives: ", 
                        font = "ArcadeClassic 40", fill = "firebrick1")
    if data.lives < 4:
        for i in range(data.lives):
            canvas.create_image(150 + i*(data.heartWidth + 10), 
                                data.height - 40, anchor = "w", 
                                image = data.heart)
    else:
        canvas.create_image(150, data.height - 40, anchor = "w", 
                            image = data.heart)
        canvas.create_text(150 + data.heartWidth + 5, data.height - 40, 
                            anchor = "w", text = "X " + str(data.lives), 
                            fill = "white", font = "ArcadeClassic 40")
    canvas.create_text(data.width - 10, data.height - 40, anchor = "e", 
                            text = "Score: " + str(data.score), 
                            font = "ArcadeClassic 40", fill = "gold")
    if data.currentMutiply > 1:
        canvas.create_text(data.width//2 - 280, data.height - 40, 
                                text = "Multiplier:   x " + \
                                str(data.currentMutiply), fill = "cyan", 
                                anchor = "w", font = "ArcadeClassic 20")
    wideTime = 0
    multiTime = 0 
    for x in data.aquiredPower:
        if x.type == 1:
            wideTime = max(wideTime, x.seconds)
        elif x.type == 2:
            multiTime = max(multiTime, x.seconds)
    if multiTime > 0:
        canvas.create_text(data.width//2 - 100, data.height - 40, 
                    text = "Multiplier    Time:  " +str(multiTime), 
                    fill = "cyan", anchor = "w", font = "ArcadeClassic 20")
    if wideTime > 0:
        canvas.create_text(data.width//2 + 200, data.height - 40, 
                    text = "Wide    Slider:  " +str(wideTime), 
                    ill = "green2", anchor = "w", font = "ArcadeClassic 20")


   

def redrawAllPlay(canvas, data):
    #Ball Position
    if data.start == True:
        canvas.create_oval(data.leftSlider + (data.lengthSlider / 2) - data.ball.radius, 
                            (data.topSlider - data.ball.radius) - data.ball.radius, 
                            data.leftSlider + (data.lengthSlider / 2) + data.ball.radius, 
                            data.topSlider, 
                            fill = '#%02x%02x%02x' % (data.ball.color[0], data.ball.color[1], data.ball.color[2]))
    else:
        canvas.create_oval(data.ball.x - data.ball.radius, 
                            data.ball.y - data.ball.radius, 
                            data.ball.x + data.ball.radius, 
                            data.ball.y + data.ball.radius, 
                            fill = '#%02x%02x%02x' % (data.ball.color[0], data.ball.color[1], data.ball.color[2]))
    
    #slider
    canvas.create_rectangle(data.leftSlider, 
                            data.topSlider, 
                            data.leftSlider + data.lengthSlider, 
                            data.topSlider + 20, 
                            fill = '#%02x%02x%02x' % (data.ball.color[0], data.ball.color[1], data.ball.color[2]))
    
    #Bricks
    if data.arcadeMode == False:
        for i in range (len(data.levels[data.currentLevel])):
            for j in range(len(data.levels[data.currentLevel][0])):
                if data.levels[data.currentLevel][i][j] != False:
                    canvas.create_image(j*data.levels[data.currentLevel][i][j].width, 
                                        i*data.levels[data.currentLevel][i][j].height, 
                                        image = data.bricks[data.levels[data.currentLevel][i][j].color], 
                                        anchor = "nw")
    else:
        for i in range (len(data.arcadeLevels[data.currentLevel])):
            for j in range(len(data.arcadeLevels[data.currentLevel][0])):
                if data.arcadeLevels[data.currentLevel][i][j] != False:
                    canvas.create_image(j*data.arcadeLevels[data.currentLevel][i][j].width, 
                                        i*data.arcadeLevels[data.currentLevel][i][j].height, 
                                        image = data.bricks[data.arcadeLevels[data.currentLevel][i][j].color], 
                                        anchor = "nw")
    
    detailsRedraw(canvas, data)
    
    #Falling parts
    for x in data.fallingPower:
        canvas.create_rectangle(x.x, x.y, x.x + x.fallingWidth, x.y + x.fallingHeight, fill = x.colorF)
    
    #Paused menu
    if data.isPaused == True:
        canvas.create_rectangle(data.width//2 - 400, data.height//2 - 200, data.width//2 + 400, data.height//2 + 200, fill = "black")
        canvas.create_text(data.width//2, data.height//2 - 150, text = "Paused", fill = "white", font = "ArcadeClassic 100 bold")
        canvas.create_text(data.width//2, data.height//2 + 75, text = """Press "r" to resume""", fill = "green2", font = "ArcadeClassic 50 bold")
        canvas.create_text(data.width//2, data.height//2 , text = """Press "q" to go to menu""", fill = "firebrick1", font = "ArcadeClassic 50 bold")


def readFile(path):
    with open(path, "rt") as f:
        return f.read()

def writeFile(path, contents):
    with open(path, "wt") as f:
        f.write(contents)

def getLeaderBoardInfo(path):
    leaderBoard = readFile(path)
    topPoints = dict()
    topNames = []
    line = 0
    for lines in leaderBoard.splitlines():
        counter = 0
        point = ""
        while lines[counter] in string.digits:
            point += lines[counter]
            counter += 1
        counter += 1
        name = lines[counter:]
        topPoints[line] = int(point)
        line += 1
        topNames.append(name)
    topTenPoints = []
    for i in range(line):
        x = max(topPoints.items(), key=lambda k: k[1])
        topTenPoints.append(x)
        del topPoints[x[0]]
    return topTenPoints[:10]

def getNames(lst):
    result = []
    for i in lst:
        indexOfSpace = i.find(" ")
        result.append(i[indexOfSpace + 1:])
    return result

def mousePressedWin(event, data):
    pass

def keyPressedWin(event, data):
    if data.nameCounter == 0:
        if event.keysym in "abcdefghijklmnopqrstuvwxyz0987654321" and len(data.name) < 3:
            data.name += event.keysym.upper()
        elif event.keysym == "BackSpace":
            data.name = data.name[:-1]
        elif event.keysym == "Return" and len(data.name) == 3:
            data.nameCounter += 1
            if data.arcadeMode == False:
                currentLeaderBoard = readFile("Leaderboard.txt")
                data.writeFile("Leaderboard.txt", 
                currentLeaderBoard + str(data.score) + " " + data.name + "\n")
            else:
                currentLeaderBoard = readFile("LeaderboardAr.txt")
                data.writeFile("LeaderboardAr.txt", 
                currentLeaderBoard + str(data.score) + " " + data.name + "\n")
            data.score = 0
            data.name = ""
    else:
        if event.keysym == "Escape":
            data.mode = "startScreen"
        elif event.keysym == "Right" or event.keysym == "Left":
            data.arcadeMode = not data.arcadeMode

    
#Flashing black and white
def timerFiredWin(data):
    data.endTime += data.timerDelay
    if data.endTime % 100 == 0:
        if data.endColor == "white":
            data.endColor = "black"
        else:
            data.endColor = "white"

#Entering name and LeaderBord
def redrawAllWin(canvas, data):
    canvas.create_rectangle(0, 0, data.width, data.height, fill = "black")
    if data.nameCounter == 0:
        if data.gameOver == True:
            canvas.create_text(data.width//2, data.height//2 - 100, 
                text = "Game Over", font = "ArcadeClassic 100", fill = "white")
        else:
            canvas.create_text(data.width//2, data.height//2 - 100, 
                text = "congratulations!", font = "ArcadeClassic 100 bold", 
                fill = "white")
        canvas.create_text(data.width//2 - 125, data.height//2, 
            text = "Enter   Name: ", font = "ArcadeClassic 100", fill = "white")
        canvas.create_text(data.width//2 - 125, data.height//2 + 50, 
            text = "(Press  enter  once  done)", fill = "white", 
            font = "ArcadeClassic 20")
        canvas.create_text(data.width//2 + 175, data.height//2, 
            text = data.name, font = "ArcadeClassic 100 bold", 
            fill = "white", anchor = "w")
        canvas.create_rectangle(data.width//2 + 175, data.height//2 + 40, 
            data.width//2 + 225, data.height//2 + 50, fill = data.endColor)
        canvas.create_rectangle(data.width//2 + 230, data.height//2 + 40, 
            data.width//2 + 280, data.height//2 + 50, fill = data.endColor)
        canvas.create_rectangle(data.width//2 + 285, data.height//2 + 40, 
            data.width//2 + 335, data.height//2 + 50, fill = data.endColor)
    else:
        canvas.create_text(50, 150, anchor = "nw", text = """Press "esc" """ , 
                        font = "ArcadeClassic 25 ", fill = "white")
        canvas.create_text(50, 175, anchor = "nw", text = "to   go   back" , 
                        font = "ArcadeClassic 25 ", fill = "white")
        canvas.create_text(data.width-50, 150, anchor = "ne", 
        text = "Press  Right \nor   Left   To\nScroll   Through\nLeaderboard", 
        font = "ArcadeClassic 25 ", fill = "white")
        if data.arcadeMode == False: 
            canvas.create_text(data.width//2, 40, text = "Reg   Leaderboard", 
                font = "ArcadeClassic 100", fill = "snow")
        else: 
            canvas.create_text(data.width//2, 40, text = "Arcade   Leaderboard",
                font = "ArcadeClassic 100", fill = "snow")
        canvas.create_text(data.width//3, 125, text = "Name", 
            font = "ArcadeClassic 50 bold", fill = "snow")
        canvas.create_text(data.width//1.5, 125, text = "Points", 
            font = "ArcadeClassic 50 bold", fill ="snow")
        if data.arcadeMode == False: 
            lst = getLeaderBoardInfo("Leaderboard.txt")
            nameLst = readFile("Leaderboard.txt")
        if data.arcadeMode == True: 
            lst = getLeaderBoardInfo("LeaderboardAr.txt")
            nameLst = readFile("LeaderboardAr.txt")
        nameLst = nameLst.splitlines()
        nameLst = getNames(nameLst)
        for i in range(len(lst)):
            nameIndex = lst[i][0]
            name = nameLst[nameIndex]
            points = lst[i][1]
            canvas.create_text(data.width//3, 200 +(i*50), 
                text = str(i + 1) + ". " + name, font = "ArcadeClassic 40", 
                fill = "white")
            canvas.create_text(data.width//1.5, 200 +(i*50), 
                text = str(points), font = "ArcadeClassic 40", 
                fill ="white")

#Buttons on main screen
def mousePressedStart(event, data):
    if 50 < event.x < data.width//2 - 50 and \
        data.height//2 - 50 < event.y < data.height//2 + 100:
        data.arcadeMode = False
        data.mode = "playScreen"
    elif 50 < event.x < data.width//2 - 50 and \
        data.height//2 + 150 < event.y < data.height//2 + 300:
        data.mode = "helpScreen"
    elif data.width//2 + 50 < event.x < data.width - 50 and \
        data.height//2 - 50 < event.y < data.height//2 + 100:
        data.arcadeMode = True
        data.mode = "playScreen"
    elif data.width//2 + 50 < event.x < data.width - 50 and \
        data.height//2 + 150 < event.y < data.height//2 + 300:
        data.mode = "endWinScreen"
        data.nameCounter = 1
    

def keyPressedStart(event, data):
    pass


def timerFiredStart(data):
    global beat
    updateVisualizer()
    if beat:
        data.startColorR = random.randint(50, 255)
        data.startColorG = random.randint(50, 255)
        data.startColorB = random.randint(50, 255)


#Draws buttons
def redrawAllStart(canvas, data):
    canvas.create_rectangle(0, 0, data.width, data.height, fill = "black")
    canvas.create_text(data.width//2, 50, text = "Audio",
        font = "ArcadeClassic 100 bold", 
        fill = '#%02x%02x%02x' % (data.startColorR, data.startColorG, data.startColorB))
    canvas.create_text(data.width//2, 125, text = "BrickBreaker",
        font = "ArcadeClassic 100 bold", 
        fill = '#%02x%02x%02x' % (data.startColorR, data.startColorG, data.startColorB))
    
    #Level Button
    canvas.create_rectangle(50, data.height//2 - 50, 
        data.width//2 - 50, data.height//2 + 100, fill = "cyan")
    canvas.create_text(data.width//4, data.height//2 + 25, 
        text = "Level   Mode", font = "ArcadeClassic 50 bold")

    #Help Screen Button
    canvas.create_rectangle(50, data.height//2 + 150, 
        data.width//2 - 50, data.height//2 + 300, fill = "green2")
    canvas.create_text(data.width//4, data.height//2 + 225, 
        text = "Help  Screen", font = "ArcadeClassic 50 bold")

    #Arcade Button
    canvas.create_rectangle(data.width//2 + 50, data.height//2 - 50, 
        data.width - 50, data.height//2 + 100, fill = "firebrick1")
    canvas.create_text(data.width * 3//4, data.height//2 + 25, 
        text = "Arcade  Mode", font = "ArcadeClassic 50 bold")

    #Leadeboard Button
    canvas.create_rectangle(data.width//2 + 50, data.height//2 + 150, 
        data.width - 50, data.height//2 + 300, fill = "purple1")
    canvas.create_text(data.width * 3//4, data.height//2 + 225, 
        text = "Leaderboard", font = "ArcadeClassic 50 bold")


def keyPressedHelp(event, data):
    if event.keysym == "Escape":
        data.mode = "startScreen"

def mousePressedHelp(event, data):
    pass

def timerFiredHelp(data):
    global beat
    updateVisualizer() 
    if beat:
        data.startColorR = random.randint(50, 255)
        data.startColorG = random.randint(50, 255)
        data.startColorB = random.randint(50, 255)

#Prints all the text in Help Menu
def redrawAllHelp(canvas, data):
    canvas.create_rectangle(0, 0, data.width, data.height, fill = "black")
    canvas.create_text(50, 50, anchor = "nw", text = """Press "esc" """ , 
        font = "ArcadeClassic 25 ", fill = "white")
    canvas.create_text(50, 75, anchor = "nw", text = "to   go   back" , 
        font = "ArcadeClassic 25 ", fill = "white")
    canvas.create_text(data.width//2, 75, text = "Help", 
        font = "ArcadeClassic 100 bold", fill = "white")
    canvas.create_text(50, 150, text = "Use   Arrow   keys   (left   or   right)   to   move", 
        fill = "white" , anchor = "nw", font = "ArcadeClassic 50")
    canvas.create_text(50, 200, text = "press   space   bar   to   shoot   ball", 
        fill = "white", anchor = "nw", font = "ArcadeClassic 50")
    canvas.create_text(50, 250, text = "press   esc   to   pause   during   game", 
        fill = "white", anchor = "nw", font = "ArcadeClassic 50")
    canvas.create_text(50, 300, text = "Green   Powerup   Widens   slider", 
        fill = "green2" , anchor = "nw", font = "ArcadeClassic 50")
    canvas.create_text(50, 350, text = "Blue   Powerup   gives   a   Multiplier", 
        fill = "cyan" , anchor = "nw", font = "ArcadeClassic 50")
    canvas.create_text(50, 400, text = "yellow   powerup   catches   ball", 
        fill = "gold" , anchor = "nw", font = "ArcadeClassic 50")
    canvas.create_text(50, 450, text = "red   powerup   gives   another   life", 
        fill = "firebrick1" , anchor = "nw", font = "ArcadeClassic 50")
    canvas.create_text(50, 500, text = "Make   noise   to   flash   color", 
        fill = '#%02x%02x%02x' % (data.startColorR, data.startColorG, data.startColorB), 
        anchor = "nw", font = "ArcadeClassic 50")
    canvas.create_text(50, 550, text = "Regular   Mode:   Five   Levels", 
        fill = "white", font = "ArcadeClassic 50", anchor = "nw")
    canvas.create_text(50, 600, text = "Arcade   Mode:   Unlimited   Levels",  
        fill = "white", font = "ArcadeClassic 50", anchor = "nw")

        


def run(width=300, height=300):
    def redrawAllWrapper(canvas, data):
        canvas.delete(ALL)
        canvas.create_rectangle(0, 0, data.width, data.height,
                                fill='white', width=0)
        redrawAll(canvas, data)
        canvas.update()    

    def mousePressedWrapper(event, canvas, data):
        mousePressed(event, data)
        redrawAllWrapper(canvas, data)

    def keyPressedWrapper(event, canvas, data):
        keyPressed(event, data)
        redrawAllWrapper(canvas, data)

    def timerFiredWrapper(canvas, data):
        timerFired(data)
        redrawAllWrapper(canvas, data)
        # pause, then call timerFired again
        canvas.after(data.timerDelay, timerFiredWrapper, canvas, data)
    # Set up data and call init
    class Struct(object): pass
    data = Struct()
    data.width = width
    data.height = height
    data.timerDelay = 10 # milliseconds
    root = Tk()
    root.resizable(width=False, height=False) # prevents resizing window
    init(data)
    # create the root and the canvas
    canvas = Canvas(root, width=data.width, height=data.height)
    canvas.configure(bd=0, highlightthickness=0)
    canvas.pack()
    # set up events
    root.bind("<Button-1>", lambda event:
                            mousePressedWrapper(event, canvas, data))
    root.bind("<Key>", lambda event:
                            keyPressedWrapper(event, canvas, data))
    timerFiredWrapper(canvas, data)
    # and launch the app
    root.mainloop()  # blocks until window is closed
    print("bye!")

run(1200, 700)