import json
import random

class RoboTaxi():

    # Initialize the RoboTaxi game
    def __init__(self):
        self.json_file = json.loads('{  "field": [    "########",    "#......#",    "#...S..#",    "#......#",    "#.P....#",    "#...C..#",    "#......#",    "########"  ],  "initial_snake_length": 1,  "max_step_limit": 200,  "rewards": {    "timestep": 0,    "good_fruit": 6,    "bad_fruit": -1,    "died": 0,    "lava": -5  }}')
        
        self.dots = self.json_file['initial_snake_length']
        self.NUM_OBJ = 2
        self.adding_obj = []
        self.cycles = 0
        self.score = 0

        self.leftDirection = False
        self.rightDirection = True
        self.upDirection = False
        self.downDirection = False

        self.C_HEIGHT = 700
        self.C_WIDTH = 700
        self.DOT_SIZE = self.C_HEIGHT / len(self.json_file['field'][0])
        self.MAX_DOTS = len(self.json_file['field'][0]) * len(self.json_file['field'])
        self.INC_VAL = 10
        self.COLLISION_TIME = 7
        self.RANDGEN_TIME = -1 * (self.COLLISION_TIME + 3)

        self.x = [0] * self.MAX_DOTS
        self.y = [0] * self.MAX_DOTS
        self.orientation = [0] * self.MAX_DOTS
        self.game_map = ['.'] * len(self.json_file['field'])
        self.accident_tracker = [0] * len(self.json_file['field'])
        self.next_transition = [1, 0]
        self.finished = False
        
        for i in range (0, len(self.json_file['field'])):
            self.game_map[i] = list(self.json_file['field'][i])
            self.accident_tracker[i] = [0] * len(self.json_file['field'][0])
            
        self.transition = [None] * self.MAX_DOTS
            
        for i in range (0, len(self.transition)):
            if i == 0:
                self.transition[i] = [1, 0]
            else :
                self.transition[i] = [1, 0]

        temp = [['C', 0], ['P', 0], ['B', 0]]

        for i in range (0, len(self.json_file['field'][0])):
            for j in range (0, len(self.json_file['field'])):
                if self.game_map[i][j] == 'S':
                    self.game_map[i][j] = '.'
                    self.create_snake(i * self.DOT_SIZE, j * self.DOT_SIZE)
                elif self.game_map[i][j] != '.' and self.game_map[i][j] != '#':
                    for k in range (0, len(temp)):
                        if temp[k][0] == self.game_map[i][j]:
                            temp[k][1] += 1

        for i in range (0, len(temp)):
            for k in range(temp[i][1], self.NUM_OBJ):
                self.random_generate(temp[i][0])
        return

    ##########################ESSENTIAL FUNCTIONS##########################
    def initial_parameters(self):
        message = {
            'C_WIDTH': self.C_WIDTH,
            'C_HEIGHT': self.C_HEIGHT,
            'score': self.score,
            'cycles': self.cycles,
            'bus': [
                {"orientation" : self.orientation[0],
                 "transition" : self.transition[0],
                 "x" : self.x[0], "y" : self.y[0]}
            ],
            'max_cycle': self.json_file['max_step_limit'],
            'map_size_x': len(self.game_map[0]),
            'map_size_y': len(self.game_map),
            'dot_size': self.DOT_SIZE
        }
        return message

    def get_render(self):
        self.move()
        self.checkCollision()
        # print("----------------------------------------------")
        # print("transition: " + str(self.transition[0]))
        # print("next_transition: " + str(self.next_transition))
        # print("up: " + str(self.upDirection))
        # print("left: " + str(self.leftDirection))
        # print("down: " + str(self.downDirection))
        # print("right: " + str(self.rightDirection))
        # print("----------------------------------------------")
        message = {
            'bus': [
                {"orientation" : self.orientation[0],
                 "transition" : self.transition[0],
                 "x" : self.x[0], "y" : self.y[0],
                 "up" : self.upDirection,
                 "left" : self.leftDirection,
                 "down" : self.downDirection,
                 "right" : self.rightDirection
                }
            ],
            'score' : self.score,
            'map' : self.game_map,
            'accident_tracker' : self.accident_tracker,
            'finished': self.finished    # determines if it's time to get and use inputs
        }
        return message

    def update(self, transition):
        self.finished = False
        self.next_transition = transition
        self.checkCollision()
        return
    ##########################ESSENTIAL FUNCTIONS##########################


    # randomly generate new game objects
    def random_generate(self, character):
        temp_bool = False

        while (temp_bool == False):
            rand1 = random.randint(0, len(self.game_map[0]) - 1)
            rand2 = random.randint(0, len(self.game_map) - 1)
            if (self.game_map[rand1][rand2] == '.'):
                self.game_map[rand1][rand2] = character
                temp_bool = True
        return
        

    def update_increments(self):
        for i in range (0, self.dots):
            # going up
            if (self.transition[i][0] == 0 and self.transition[i][1] < 0):
                self.transition[i][1] -= self.INC_VAL
            # going down
            elif (self.transition[i][0] == 0 and self.transition[i][1] > 0):
                self.transition[i][1] += self.INC_VAL
            # going to the right
            elif (self.transition[i][0] > 0 and self.transition[i][1] == 0):
                self.transition[i][0] += self.INC_VAL
            # going to the left
            elif (self.transition[i][0] < 0 and self.transition[i][1] == 0):
                self.transition[i][0] -= self.INC_VAL
        return

    # create the head and body of the snake
    def create_snake(self, startx, starty):
        for z in range (0, self.dots):
            self.x[z] = startx - (z * self.DOT_SIZE)
            self.y[z] = starty
            self.orientation[z] = 3
        return

    def reset(self):
        # every sprite aside from the first dot gets updated by a frame
        for z in range (self.dots, 0, -1):
            self.x[z] = self.x[(z - 1)];
            self.y[z] = self.y[(z - 1)];
            self.orientation[z] = self.orientation[(z - 1)];
            self.transition[z] = self.transition[(z - 1)];
            temp_sum = abs(self.transition[z][0] + self.transition[z][1]);
            self.transition[z] = [self.transition[z][0] * (1 / temp_sum),
                                  self.transition[z][1] * (1 / temp_sum)]

        # update timestep
        self.score += self.json_file['rewards']['timestep']
        self.cycles += 1
        self.finished = True

        if (self.next_transition[0] == -1):
            self.leftDirection = True
            self.upDirection = False
            self.downDirection = False
        elif (self.next_transition[0] == 1):
            self.rightDirection = True
            self.upDirection = False
            self.downDirection = False
        elif (self.next_transition[1] == -1):
            self.upDirection = True
            self.rightDirection = False
            self.leftDirection = False
        elif (self.next_transition[1] == 1):
            self.downDirection = True
            self.rightDirection = False
            self.leftDirection = False

        # get the right transition array
        temp_array = [0, 0]
        if self.next_transition[0] == 0:
            temp_array[0] = 0
        elif self.next_transition[0] > 0:
            temp_array[0] = 1
        else:
            temp_array[0] = -1

        if self.next_transition[1] == 0:
            temp_array[1] = 0
        elif self.next_transition[1] > 0:
            temp_array[1] = 1
        else:
            temp_array[1] = -1
        
        self.transition[0] = temp_array

        return
    
    def move(self):
        #check if the snake is within the bounds to move a step in a given direction
        #going to the left
        if (self.transition[0][0] < 0):
            self.orientation[0] = 1
            self.update_increments()
            if (abs(self.transition[0][0]) > self.DOT_SIZE):
                self.reset()
                self.x[0] -= self.DOT_SIZE
                
        #going to the right
        if (self.transition[0][0] > 0):
            self.orientation[0] = 3
            self.update_increments()
            if (abs(self.transition[0][0]) > self.DOT_SIZE ):
                self.reset()
                self.x[0] += self.DOT_SIZE

        #going up
        if (self.transition[0][1] < 0):
            self.orientation[0] = 0
            self.update_increments()
            if (abs(self.transition[0][1]) > self.DOT_SIZE):
                self.reset()
                self.y[0] -= self.DOT_SIZE

        #going down
        if (self.transition[0][1] > 0):
            self.orientation[0] = 2
            self.update_increments()
            if (abs(self.transition[0][1]) > self.DOT_SIZE):
                self.reset()
                self.y[0] += self.DOT_SIZE

        return

    def checkCollision(self):
        for z in range(self.dots, 0, -1):

            # snake bit itself or is outside of the bounds
            if ((z > 4) and (self.x[0] == self.x[z]) and (self.y[0] == self.y[z])):
                self.cycles = self.json_file['max_step_limit']

            # make sure to check if in game so as to not violate array ranges
            tempX = int(self.x[0] / self.DOT_SIZE)
            tempY = int(self.y[0] / self.DOT_SIZE)
                
            if (tempX == 1 and self.leftDirection or tempX == len(self.game_map[0]) - 2 and self.rightDirection):
                self.transition[0][0] = 0

                self.leftDirection = False
                self.rightDirection = False
                if (tempY < len(self.game_map[0]) / 2):
                    self.transition[0][1] = 1
                    self.downDirection = True
                else:
                    self.transition[0][1] = -1
                    self.upDirection = False
                    self.next_transition = self.transition[0]

            if (tempY == 1 and self.upDirection or tempY == len(self.game_map[0]) - 2 and self.downDirection):
                self.transition[0][1] = 0
                self.upDirection = False
                self.downDirection = False
                if (tempX < len(self.game_map[0]) / 2):
                    self.transition[0][0] = 1
                    self.rightDirection = True
                else:
                    self.transition[0][0] = -1
                    self.leftDirection = True
                    self.next_transition = self.transition[0]

            # check if there's been an accident/update with any of the game objects
            if (self.game_map[tempX][tempY] == 'C' and self.accident_tracker[tempX][tempY] == 0):
                # bus is on a car tile
                self.score += self.json_file['rewards']['lava']
                self.adding_obj.append([self.RANDGEN_TIME, "C"])
                self.accident_tracker[tempX][tempY] = self.COLLISION_TIME         # 7 denotes the amount of cycles for this entity to fade away
            elif (self.game_map[tempX][tempY] == 'P' and self.accident_tracker[tempX][tempY] == 0):
                # bus picked up a person			
                self.score += self.json_file['rewards']['good_fruit']
                self.adding_obj.append([self.RANDGEN_TIME, "P"])
                self.accident_tracker[tempX][tempY] = self.COLLISION_TIME
            elif (self.game_map[tempX][tempY] == 'B' and self.accident_tracker[tempX][tempY] == 0):
                # bus ran into a road stop		
                self.score += self.json_file['rewards']['bad_fruit']
                self.adding_obj.append([self.RANDGEN_TIME, "B"])
                self.accident_tracker[tempX][tempY] = self.COLLISION_TIME	
            elif (self.game_map[tempX][tempY] == '#' and self.accident_tracker[tempX][tempY] == 0):
                # bus hit a forest
                self.score += self.json_file['rewards']['died']
                self.accident_tracker[tempX][tempY] = self.COLLISION_TIME

            # iterate thorugh the entire map to check if any can be removed due to fade time elapsing
            for i in range (0, len(self.game_map)):
                for j in range (0, len(self.game_map[0])):
                    if (self.accident_tracker[i][j] != 0):
                        if (self.accident_tracker[i][j] == 1):
                            self.game_map[i][j] = '.'
                        self.accident_tracker[i][j] -= 1

            temp_array = []
            for i in range (0, len(self.adding_obj)):
                self.adding_obj[i][0] += 1
                if (self.adding_obj[i][0] == 0):
                    self.random_generate(self.adding_obj[i][1])
                else:
                    temp_array.append(self.adding_obj[i])

            self.adding_obj = temp_array
            return
