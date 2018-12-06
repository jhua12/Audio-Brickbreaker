import math
import random

#######################
# Objects used in games
#######################

#Normal Brick
class Brick(object):
    def __init__(self):
        self.color = random.randint(0, 7)
        self.width = 120
        self.height = 40
        self.type = 0

#Special Brick
class PowerBrick(object):
    def __init__(self):
        self.width = 120
        self.height = 40
        self.color = random.randint(0, 7)
        self.fallingWidth = 30
        self.fallingHeight = 10
        self.speed = 5
        self.x = 0
        self.y = 0

#Widen Slider power up
class WideSlider(PowerBrick):
    def __init__(self):
        super().__init__()
        #increases by 40
        self.seconds = 10
        self.type = 1
        self.colorF = "green2"

#Multiplier power up
class Multiplier(PowerBrick):
    def __init__(self):
        super().__init__()
        self.mutiply = random.randint(2, 4)
        self.seconds = 10
        self.type = 2
        self.colorF = "cyan"

#Catch power up
class Catch(PowerBrick):
    def __init__(self):
        super().__init__()
        self.type = 3
        self.colorF = "gold"

#Extra life power up
class Life(PowerBrick):
    def __init__(self):
        super().__init__()
        self.type = 4
        self.colorF = "firebrick1"

class Ball(object):
    def __init__(self):
        self.x = 600
        self.y = 300
        self.angle = 0 - (math.pi * 2) / 4
        self.radius = 13
        self.color = [0, 0, 0]
        self.speed = 10