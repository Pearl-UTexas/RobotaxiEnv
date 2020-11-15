import random
import copy
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import json

from robotaxi.agent import AgentBase
from robotaxi.gameplay.entities import CellType, Point, SnakeAction, SnakeDirection, ALL_SNAKE_ACTIONS, ALL_SNAKE_DIRECTIONS
from robotaxi.gameplay.environment import Environment

class ValueIterationAgent(AgentBase):
    """ Represents a Snake agent that runs value iteration at every step (when nothing was eaten). """

    def __init__(self, grid_size=8, discount=0.95, reward_mapping=None, env=None, level_file='./RoboTaxiEnv/robotaxi/levels/8x8-blank.json'):
        # 18 * 18 (gridsize-2) * 4 (four directions)
        self.grid_size = grid_size
        self.env = env if env is not None else Environment(config=json.load(open(level_file)), stationary=False)

        self.level_map = self.env.field.level_map
        self.num_states = ((grid_size-2)**2)*len(ALL_SNAKE_DIRECTIONS)
        self.num_actions = len(ALL_SNAKE_ACTIONS)
        self.transition_function = [] # s' = T(s,a) s -> <i,j,k>
        self.V_estimations = [] # v = V(s) -> V(<i,j,k>)
        self.discount = discount

        self.level_map_to_cell_type = {
            'S': CellType.SNAKE_HEAD,
            's': CellType.SNAKE_BODY,
            '#': CellType.WALL,
            'O': CellType.GOOD_FRUIT,
            '.': CellType.EMPTY,
            'o': CellType.BAD_FRUIT,
            '!': CellType.LAVA,
            'P': CellType.PIT,
            'C': CellType.COLLABORATOR_HEAD,
            'c': CellType.COLLABORATOR_BODY
        }
        self.cells = np.array([
                [self.level_map_to_cell_type[symbol] for symbol in line]
                for line in self.level_map
            ])
        self.initialize_transition_function()
        self.data_to_cell_type = {
            0: CellType.EMPTY,
            1: CellType.GOOD_FRUIT,
            2: CellType.BAD_FRUIT,
            3: CellType.LAVA,
            4: CellType.SNAKE_HEAD,
            5: CellType.SNAKE_BODY,
            6: CellType.WALL,
            7: CellType.PIT,
            8: CellType.COLLABORATOR_HEAD,
            9: CellType.COLLABORATOR_BODY
        }
        if reward_mapping is None:
            self.reward_mapping = {
                CellType.SNAKE_HEAD: 0,
                CellType.SNAKE_BODY: 0,
                CellType.COLLABORATOR_HEAD: 0,
                CellType.COLLABORATOR_BODY: 0,
                CellType.GOOD_FRUIT: 6,
                CellType.BAD_FRUIT: -1,
                CellType.LAVA: -5,
                CellType.EMPTY: 0,
                CellType.PIT: 0,
                CellType.WALL: -100,
            }
        else:
            #self.reward_mapping = reward_mapping
            self.set_reward_mapping(reward_mapping)
        self.last_reward = 0.0
        self.last_pickup = None
        self.last_frame = None
        self.env_changed = True
        for i in range(1,self.grid_size-1):
            self.V_estimations.append([])
            for j in range(1,self.grid_size-1):
                self.V_estimations[i-1].append({})
                for k in ALL_SNAKE_DIRECTIONS:
                    self.V_estimations[i-1][j-1][k] = 0.0

    def update_env(self, env):
        self.env = env
        self.level_map = self.env.field.level_map
        self.cells = np.array([
                [self.level_map_to_cell_type[symbol] for symbol in line]
                for line in self.level_map
            ])
        self.initialize_transition_function()
        
    def begin_episode(self):
        pass
    
    def get_cell(self, point):
        """ Get the type of cell at the given point. """
        x, y = point
        return self.cells[y, x]

    def get_q_value(self, state, action):
        s_prime = self.transition_function[state[0]-1][state[1]-1][state[2]][action]
        q_val = self.curr_reward_map[s_prime[0]][s_prime[1]] + self.discount * self.V_estimations[s_prime[0]-1][s_prime[1]-1][s_prime[2]]
        return q_val
        
    def value_iteration(self, epsilon=0.05, print_val_map=False):
        
        # require reward_map already computed
        # skip init -> warm start from previous value estimations

        while True:
            delta = 0.0
            for i in range(1,self.grid_size-1):
                for j in range(1,self.grid_size-1):
                    for k in ALL_SNAKE_DIRECTIONS:
                        if self.curr_reward_map[i][j] == self.reward_mapping[CellType.WALL]:
                            self.V_estimations[i-1][j-1][k] = float("-inf")
                        else:
                            max_action_val = float("-inf")
                            for action in ALL_SNAKE_ACTIONS:
                                s_prime = self.transition_function[i-1][j-1][k][action]
                                peek_reward = self.curr_reward_map[s_prime[0]][s_prime[1]]
                                exp_util = peek_reward + self.discount * self.V_estimations[s_prime[0]-1][s_prime[1]-1][s_prime[2]]
                                if exp_util > max_action_val: max_action_val = exp_util

                            new_estimation = max_action_val
                            abs_diff = abs(new_estimation - self.V_estimations[i-1][j-1][k])
                            if abs_diff > delta: delta = abs_diff
                            self.V_estimations[i-1][j-1][k] = new_estimation

            if delta < epsilon: break
       
        if print_val_map:
            value_map = []
            for i in range(1,self.grid_size-1):
                ith_row = []
                for j in range(1,self.grid_size-1):
                    ith_row.append(-100.0)
                    for k in ALL_SNAKE_DIRECTIONS:
                        ith_row[-1]=round(max(ith_row[-1],self.V_estimations[i-1][j-1][k]),3)
                #print(ith_row)
                value_map.append(ith_row)
            # plot max value map
            value_map = np.array(value_map)
            plt.imshow(value_map)
            plt.pause(0.0001)
    
    def set_reward_mapping(self, reward_mapping):
        self.reward_mapping = reward_mapping
        if not CellType.SNAKE_HEAD in self.reward_mapping:
            self.reward_mapping[CellType.SNAKE_HEAD] = 0
            self.reward_mapping[CellType.SNAKE_BODY] = 0
        if not CellType.COLLABORATOR_HEAD in self.reward_mapping:
            self.reward_mapping[CellType.COLLABORATOR_HEAD] = 0
            self.reward_mapping[CellType.COLLABORATOR_BODY] = 0
      
    def compute_reward_map(self, observation):
        #print()
        #print(observation)
        self.curr_reward_map = []
        state_x = 0
        state_y = 0 
        state_direction = None
        self.last_pickup = None
        for x in range(len(observation)):
            self.curr_reward_map.append([])
            for y in range(len(observation[x])):
                self.curr_reward_map[-1].append(self.reward_mapping[self.data_to_cell_type[observation[x][y]]])
                if not self.env.collaboration:
                    if self.data_to_cell_type[observation[x][y]] == CellType.SNAKE_HEAD:
                        state_x = x
                        state_y = y
                        if self.data_to_cell_type[observation[x-1][y]] == CellType.SNAKE_BODY:
                            state_direction = SnakeDirection.SOUTH
                        elif self.data_to_cell_type[observation[x+1][y]] == CellType.SNAKE_BODY:
                            state_direction = SnakeDirection.NORTH
                        elif self.data_to_cell_type[observation[x][y-1]] == CellType.SNAKE_BODY:
                            state_direction =SnakeDirection.EAST
                        elif self.data_to_cell_type[observation[x][y+1]] == CellType.SNAKE_BODY:
                            state_direction = SnakeDirection.WEST
                        else:
                            print("No snake body detected!!!!!") # shouldn't be here

                        if (not self.last_frame is None) and (self.data_to_cell_type[self.last_frame[x][y]] == CellType.GOOD_FRUIT or self.data_to_cell_type[self.last_frame[x][y]] == CellType.BAD_FRUIT or self.data_to_cell_type[self.last_frame[x][y]] == CellType.LAVA):
                            self.env_changed = True
                            self.last_pickup = self.data_to_cell_type[self.last_frame[x][y]] 
                    elif (not self.env_changed) and self.data_to_cell_type[observation[x][y]] != self.data_to_cell_type[self.last_frame[x][y]]: # cell type changed
                        if self.data_to_cell_type[observation[x][y]] != CellType.SNAKE_BODY and self.data_to_cell_type[self.last_frame[x][y]] != CellType.SNAKE_BODY: #not snake_body 
                            self.env_changed = True
                            
                
                else:
                    if self.data_to_cell_type[observation[x][y]] == CellType.COLLABORATOR_HEAD:
                        state_x = x
                        state_y = y
                        if self.data_to_cell_type[observation[x-1][y]] == CellType.COLLABORATOR_BODY:
                            state_direction = SnakeDirection.SOUTH
                        elif self.data_to_cell_type[observation[x+1][y]] == CellType.COLLABORATOR_BODY:
                            state_direction = SnakeDirection.NORTH
                        elif self.data_to_cell_type[observation[x][y-1]] == CellType.COLLABORATOR_BODY:
                            state_direction =SnakeDirection.EAST
                        elif self.data_to_cell_type[observation[x][y+1]] == CellType.COLLABORATOR_BODY:
                            state_direction = SnakeDirection.WEST
                        else:
                            print("No collaborator body detected!!!!!") # shouldn't be here
                            if self.data_to_cell_type[observation[x-1][y]] == CellType.SNAKE_HEAD:
                                state_direction = SnakeDirection.SOUTH
                            elif self.data_to_cell_type[observation[x+1][y]] == CellType.SNAKE_HEAD:
                                state_direction = SnakeDirection.NORTH
                            elif self.data_to_cell_type[observation[x][y-1]] == CellType.SNAKE_HEAD:
                                state_direction =SnakeDirection.EAST
                            elif self.data_to_cell_type[observation[x][y+1]] == CellType.SNAKE_HEAD:
                                state_direction = SnakeDirection.WEST
                            else:
                                if self.data_to_cell_type[observation[x-1][y]] == CellType.SNAKE_BODY:
                                    state_direction = SnakeDirection.SOUTH
                                elif self.data_to_cell_type[observation[x+1][y]] == CellType.SNAKE_BODY:
                                    state_direction = SnakeDirection.NORTH
                                elif self.data_to_cell_type[observation[x][y-1]] == CellType.SNAKE_BODY:
                                    state_direction =SnakeDirection.EAST
                                elif self.data_to_cell_type[observation[x][y+1]] == CellType.SNAKE_BODY:
                                    state_direction = SnakeDirection.WEST
                    elif (not self.env_changed) and self.data_to_cell_type[observation[x][y]] != self.data_to_cell_type[self.last_frame[x][y]]:
                        if self.data_to_cell_type[observation[x][y]] != CellType.COLLABORATOR_BODY and self.data_to_cell_type[self.last_frame[x][y]] != CellType.COLLABORATOR_BODY: 
                            self.env_changed = True
        #print("curr state",state_x,state_y,state_direction)        
        #for row in self.curr_reward_map:
        #    print(row)
        self.curr_state = [state_x,state_y,state_direction]
        return self.curr_reward_map, 

    def act_on_observations(observations):
        actions = []
        for observation in observations:
            self.env_changed = True
            actions.append(self.act(observation))
        return actions


    def act(self, observation, reward=0.0, recompute=False):        
        
        self.compute_reward_map(observation)
        if self.env_changed or recompute:
            self.value_iteration(print_val_map=False)
            #print()
        # select action
        selected_action = random.choice(ALL_SNAKE_ACTIONS)        
        curr_max_val = float("-inf")
        for action in ALL_SNAKE_ACTIONS:
            '''s_prime = self.transition_function[state_x-1][state_y-1][state_direction][action]
            peek_reward = self.curr_reward_map[s_prime[0]][s_prime[1]]
            exp_util = peek_reward + self.discount * self.V_estimations[s_prime[0]-1][s_prime[1]-1][s_prime[2]]'''
            exp_util = self.get_q_value(self.curr_state, action)
            if exp_util > curr_max_val:
                curr_max_val = exp_util
                selected_action = action

        self.last_reward = reward
        self.last_frame = observation
        self.env_changed = False
        return selected_action

    def end_episode(self):
        pass

    def peek_next_move(self, head, direction):
        return head + direction

    def initialize_transition_function(self):
        if self.env.collaboration:
            wall_types = [CellType.WALL, CellType.SNAKE_HEAD, CellType.SNAKE_BODY]
        else:
            wall_types = [CellType.WALL, CellType.COLLABORATOR_HEAD]

        for i in range(1,self.grid_size-1):
            self.transition_function.append([])
            for j in range(1,self.grid_size-1):
                self.transition_function[i-1].append({})
                for k in ALL_SNAKE_DIRECTIONS:
                    self.transition_function[i-1][j-1][k] = [()]*len(ALL_SNAKE_ACTIONS)

                    if k == SnakeDirection.NORTH:
                        self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i-1,j,SnakeDirection.NORTH)
                        self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i,j-1,SnakeDirection.WEST)
                        self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i,j+1,SnakeDirection.EAST)
                        
                        # if i == 1:
                        if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.NORTH)) in wall_types:
                            if j < self.grid_size/2: # turn right
                                self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i,j+1,SnakeDirection.EAST)
                            else: # turn left
                                self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i,j-1,SnakeDirection.WEST)
                        # if j == 1:
                        if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.WEST)) in wall_types:
                            # if i == 1:
                            if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.NORTH)) in wall_types:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i,j+1,SnakeDirection.EAST)
                            else:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i-1,j,SnakeDirection.NORTH)
                        # if j == self.grid_size-2:
                        if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.EAST)) in wall_types: 
                            # if i == 1:
                            if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.NORTH)) in wall_types:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i,j-1,SnakeDirection.WEST)
                            else:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i-1,j,SnakeDirection.NORTH)

                    elif k == SnakeDirection.EAST:
                        self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i,j+1,SnakeDirection.EAST)
                        self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i-1,j,SnakeDirection.NORTH)
                        self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i+1,j,SnakeDirection.SOUTH)
                        
                        # if i == 1:
                        if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.NORTH)) in wall_types:
                            # if j == self.grid_size-2:
                            if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.EAST)) in wall_types: 
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i+1,j,SnakeDirection.SOUTH) # at corner
                            else:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i,j+1,SnakeDirection.EAST)
                        # if i == self.grid_size-2:
                        if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.SOUTH)) in wall_types: 
                            # if j == self.grid_size-2:
                            if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.EAST)) in wall_types: 
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i-1,j,SnakeDirection.NORTH)
                            else:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i,j+1,SnakeDirection.EAST)
                        # if j == self.grid_size-2:
                        if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.EAST)) in wall_types: 
                            if i < self.grid_size/2:
                                self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i+1,j,SnakeDirection.SOUTH)
                            else: # turn left
                                self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i-1,j,SnakeDirection.NORTH)
                            
                    elif k == SnakeDirection.SOUTH:
                        self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i+1,j,SnakeDirection.SOUTH)
                        self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i,j+1,SnakeDirection.EAST)
                        self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i,j-1,SnakeDirection.WEST)
                        
                        # if i == self.grid_size-2:
                        if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.SOUTH)) in wall_types: 
                            if j < self.grid_size/2: # turn right
                                self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i,j+1,SnakeDirection.EAST)
                            else: # turn left
                                self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i,j-1,SnakeDirection.WEST)
                        # if j == 1:
                        if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.WEST)) in wall_types:
                            # if i == self.grid_size-2:
                            if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.SOUTH)) in wall_types:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i,j+1,SnakeDirection.EAST)
                            else:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i+1,j,SnakeDirection.SOUTH)
                        # if j == self.grid_size-2:
                        if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.EAST)) in wall_types:
                            # if i == self.grid_size-2:
                            if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.SOUTH)) in wall_types:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i,j-1,SnakeDirection.WEST)
                            else:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i+1,j,SnakeDirection.SOUTH)

                    elif k == SnakeDirection.WEST:
                        self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i,j-1,SnakeDirection.WEST)
                        self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i+1,j,SnakeDirection.SOUTH)
                        self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i-1,j,SnakeDirection.NORTH)  
                        
                        # if i == 1:
                        if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.NORTH)) in wall_types:
                            # if j == 1:
                            if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.WEST)) in wall_types:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] =  (i+1,j,SnakeDirection.SOUTH)
                            else:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i,j-1,SnakeDirection.WEST)
                        # if i == self.grid_size-2:
                        if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.SOUTH)) in wall_types:
                            # if j == 1:
                            if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.WEST)) in wall_types:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i-1,j,SnakeDirection.NORTH) # at corner
                            else:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i,j-1,SnakeDirection.WEST)
                        # if j == 1:
                        if self.get_cell(self.peek_next_move(Point(j, i), SnakeDirection.WEST)) in wall_types:                      
                            if i < self.grid_size/2:
                                self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i+1,j,SnakeDirection.SOUTH)
                            else: # turn left
                                self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i-1,j,SnakeDirection.NORTH)
                            
        #print(len(self.transition_function),len(self.transition_function[0]),len(self.transition_function[0][0]),len(self.transition_function[0][0][SnakeDirection.SOUTH]))
