import time
import os

class Replay():

    def __init__(self):
        self.override = False          # Needed to update inputs from server -> game
        self.leftDirection = False
        self.rightDirection = False
        self.upDirection = False
        self.downDirection = False
        self.start_time = time.time()

        basedir = os.path.abspath(os.path.dirname(__file__))
        data_file = os.path.join(basedir, 'static/episode_0.record')
        self.file_array = []

        with open(data_file, "r") as file:
            for line in file.readlines():
                self.file_array.append(line.split("\n")[0])

        # create the timestep parameters
        self.cycles = 0
        self.max_step_limit = int(self.file_array[0].split(":")[1])
        self.score = 0

        # dimensions of the canvas for proper rendering
        self.C_HEIGHT = 700
        self.C_WIDTH = 700
        self.DOT_SIZE = self.C_HEIGHT / 8   # 8 is the dimensions of the map

        # collision time to record how many timesteps it takes to show how long
        # it takes for a coin or a crash icon should show
        self.COLLISION_TIME = 3
        self.RANDGEN_TIME = -1 * (self.COLLISION_TIME + 3)

        # records this timestep's bus position
        (self.this_game_map, self.this_bus_x, self.this_bus_y, self.reward, self.curr_direc, self.accident_tracker) = self.process_file_game(0)
        self.score += self.reward

        # get the next timestep because of direction discrepency ._.
        (self.next_game_map, self.next_bus_x, self.next_bus_y, self.next_reward, self.next_direc, self.next_accident) = self.process_file_game(1)

        # determine the correct orientation
        self.curr_orientation = self.determine_orientation(self.curr_direc)
        self.next_orientation = self.determine_orientation(self.next_direc)

        return

    def determine_orientation(self, orientation):
        # go up == 0
        if orientation == [0, -1]:
            return 0
        # go left == 1
        elif orientation == [-1, 0]:
            return 1
        # go down == 2
        elif orientation == [0, 1]:
            return 2
        # go right == 3
        elif orientation == [1, 0]:
            return 3

        return -1

    def process_file_game(self, codeblock):

        file_start = (15 * codeblock) + 2
        
        # read the 14 lines per block
        game_state = [None] * 15
        game_map = [None] * 8
        for i in range(0, 15):
            game_state[i] = self.file_array[file_start + i]
            # create game_map to be splitted
            if (i < 8):
                game_map[i] = list(game_state[i])

        # transpose
        game_map = [[game_map[j][i] for j in range(len(game_map))] for i in range(len(game_map[0]))]
        
        # get the reward for this timestep
        reward = int(game_state[8].split("=")[1])
        direction = game_state[12].split(":")[1]
        direction = direction.split("(")[1].split(")")
        direction = direction[0].split(",")
        direction = [int(direction[0]), int(direction[1])]

        # create accident tracker
        accident_tracker = [0] * 8
        for i in range(0, 8):
            accident_tracker[i] = [0] * 8
        
        # change the map to proper values
        # 1 - passengers
        # 2 - stop sign barricade thing
        # 3 - car crash
        # 4 - bus
        # 5 - also bus???
        # 6 - forest
        for i in range (0, 8):
            for j in range (0, 8):
                # forest
                if game_map[i][j] == "6":
                    game_map[i][j] = "#"
                elif game_map[i][j] == "5":
                    game_map[i][j] = "."
                # bus
                elif game_map[i][j] == "4":
                    # found bus location
                    bus_x = i * self.DOT_SIZE
                    bus_y = j * self.DOT_SIZE
                    if reward != 0:
                        # append to accident tracker
                        accident_tracker[i][j] = self.COLLISION_TIME
                        if reward == -5:
                            game_map[i][j] = "C"
                        if reward == -1:
                            game_map[i][j] = "B"
                        if reward == 6:
                            game_map[i][j] = "P"
                    else:
                        game_map[i][j] = "."
                # car
                elif game_map[i][j] == "3":
                    game_map[i][j] = "C"
                # road block
                elif game_map[i][j] == "2":
                    game_map[i][j] = "B"
                # passenger
                elif game_map[i][j] == "1":
                    game_map[i][j] = "P"
                elif game_map[i][j] == "0":
                    game_map[i][j] = "."

        #return the values needed for recreation
        return game_map, bus_x, bus_y, reward, direction, accident_tracker

    ##########################ESSENTIAL FUNCTIONS##########################
    def initial_parameters(self):
        message = {
            'C_WIDTH': self.C_WIDTH,
            'C_HEIGHT': self.C_HEIGHT,
            'score': self.score,
            'cycles': self.cycles,
            'max_cycle': self.max_step_limit,
            'map_size_x': len(self.this_game_map[0]),
            'map_size_y': len(self.this_game_map),
            'dot_size': self.DOT_SIZE,
            'bus': [
                {"orientation" : self.curr_orientation,
                 "transition" : self.next_direc,  # direction with next timestep
                 "x" : self.this_bus_x, "y" : self.this_bus_y,
                 "up" : self.upDirection,
                 "left" : self.leftDirection,
                 "down" : self.downDirection,
                 "right" : self.rightDirection
                }
            ],
            'score' : self.score,
            'map' : self.this_game_map,
            'accident_tracker' : self.accident_tracker,
            'next_transition' : self.next_direc,      #basically throaway
            'override' : self.override
        }
        return message

    def update(self):

        # update the score
        self.score += self.next_reward
        ret = {
            'bus': [
                {"orientation" : self.curr_orientation,
                 "transition" : self.next_direc,
                 "x" : self.this_bus_x, "y" : self.this_bus_y,
                 "up" : self.upDirection,
                 "left" : self.leftDirection,
                 "down" : self.downDirection,
                 "right" : self.rightDirection
                }
            ],
            'score' : self.score,
            'map' : self.this_game_map,
            'accident_tracker' : self.accident_tracker,
            'next_transition' : self.next_direc,
            'override' : self.override
        }

        # update the timestep
        self.cycles += 1

        # update accident_tracker information
        for i in range(0, 8):
            for j in range(0, 8):
                if self.accident_tracker[i][j] != 0:
                    if self.reward == -5:
                        self.next_game_map[i][j] = "C"
                    elif self.reward == -1:
                        self.next_game_map[i][j] = "B"
                    elif self.reward == 6:
                        self.next_game_map[i][j] = "P"
                    else :
                        self.next_game_map[i][j] = self.this_game_map[i][j]
                    self.accident_tracker[i][j] -= 1
                    if self.accident_tracker[i][j] == 0 or self.accident_tracker[i][j] == 1:
                        self.next_game_map[i][j] = "."
                        
                self.accident_tracker[i][j] += self.next_accident[i][j]

        # update the next timestep into current timestep
        self.this_game_map = self.next_game_map
        self.this_bus_x = self.next_bus_x
        self.this_bus_y = self.next_bus_y
        self.curr_direc = self.next_direc
        self.curr_orientation = self.next_orientation
        self.reward = self.next_reward

        # check if this is the (n - 1) timestep
        if self.cycles + 1 < self.max_step_limit:
            (self.next_game_map, self.next_bus_x, self.next_bus_y, self.next_reward, self.next_direc, self.next_accident) = self.process_file_game(self.cycles + 1)

            # determine the correct orientation
            self.next_orientation = self.determine_orientation(self.next_direc)

        return ret

    def clear(self):
        # return the start time
        return time.time() - self.start_time
