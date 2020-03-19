import random
import copy
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

from robotaxi.agent import AgentBase
from robotaxi.gameplay.entities import CellType, Point, SnakeAction, SnakeDirection, ALL_SNAKE_ACTIONS, ALL_SNAKE_DIRECTIONS


class TileCodingAgent(AgentBase):
    """ Represents a Snake agent that runs value iteration at every step (when nothing was eaten). """

    def __init__(self, grid_size=8, discount=0.95, reward_mapping=None, weights=None):
        # 18 * 18 (gridsize-2) * 4 (four directions)
        self.grid_size = grid_size
        self.num_states = ((grid_size-2)**2)*len(ALL_SNAKE_DIRECTIONS)
        self.num_actions = len(ALL_SNAKE_ACTIONS)
        self.transition_function = [] # s' = T(s,a) s -> <i,j,k>
        self.initialize_transition_function()
        self.discount = discount

        self.feature_ranges = [[-grid_size, grid_size], [-grid_size, grid_size]]  # 2 features
        self.number_tilings = 3
        self.bins = [[4, 4], [4, 4], [4, 4]]  # each tiling has a 10*10 grid
        self.offsets = [[0, 0], [-2, -2], [2, 2]]
        self.tilings = self.create_tilings()
        self.tile_features = np.zeros((self.number_tilings, 3, self.bins[0][0],self.bins[0][1]))
        self.weights = np.zeros((self.number_tilings, 3, self.bins[0][0],self.bins[0][1]))
        if weights is not None:
            self.parse_weights_file(weights)

        self.data_to_cell_type = {
            0: CellType.EMPTY,
            1: CellType.GOOD_FRUIT,
            2: CellType.BAD_FRUIT,
            3: CellType.LAVA,
            4: CellType.SNAKE_HEAD,
            5: CellType.SNAKE_BODY,
            6: CellType.WALL,
            7: CellType.DUMMY,
        }
        if reward_mapping is None:
            self.reward_mapping = {
                CellType.SNAKE_HEAD: 0,
                CellType.SNAKE_BODY: 0,
                CellType.GOOD_FRUIT: 20,
                CellType.BAD_FRUIT: -10,
                CellType.LAVA: -50,
                CellType.EMPTY: -1,
                CellType.WALL: -20,
            }
        else:
            self.reward_mapping = reward_mapping
        self.last_reward = 0.0
        self.last_frame = None
        self.env_changed = True

    def parse_weights_file(self, weights_file):
        line_ct = 0
        feature_data = []
        tiling_index = 0
        cell_type = 0

        weight_file_handle = open(weights_file)

        for line in weight_file_handle:
            if "," in line:
                feature_data.append([float(i) for i in line.split(",")])
                line_ct += 1

            if line.startswith('Tiling'):
                tiling_index = eval(line.strip().split(':')[1])

            if line.startswith('Cell_type'):
                cell_type = eval(line.strip().split(':')[1])

            if line_ct == self.bins[tiling_index][0]:
                line_ct = 0
                self.weights[tiling_index, cell_type] = np.asarray(list(feature_data))
                feature_data = []
        print (self.weights)
        
    def begin_episode(self):
        pass
    
    def create_tiling(self, feat_range, bins, offset):
        """
        Create 1 tiling spec of 1 dimension(feature)
        feat_range: feature range; example: [-1, 1]
        bins: number of bins for that feature; example: 10
        offset: offset for that feature; example: 0.2
        """
    
        return np.linspace(feat_range[0], feat_range[1], bins+1)[1:-1] + offset

    def create_tilings(self):
        """
        feature_ranges: range of each feature; example: x: [-1, 1], y: [2, 5] -> [[-1, 1], [2, 5]]
        number_tilings: number of tilings; example: 3 tilings
        bins: bin size for each tiling and dimension; example: [[10, 10], [10, 10], [10, 10]]: 3 tilings * [x_bin, y_bin]
        offsets: offset for each tiling and dimension; example: [[0, 0], [0.2, 1], [0.4, 1.5]]: 3 tilings * [x_offset, y_offset]
        """
        tilings = []
        # for each tiling
        for tile_i in range(self.number_tilings):
            tiling_bin = self.bins[tile_i]
            tiling_offset = self.offsets[tile_i]
            
            tiling = []
            # for each feature dimension
            for feat_i in range(len(self.feature_ranges)):
                feat_range = self.feature_ranges[feat_i]
                # tiling for 1 feature
                feat_tiling = self.create_tiling(feat_range, tiling_bin[feat_i], tiling_offset[feat_i])
                tiling.append(feat_tiling)
            tilings.append(tiling)
        return np.array(tilings)

    def get_tile_coding(self, feature):
        """
        feature: sample feature with multiple dimensions that need to be encoded; example: [0.1, 2.5], [-0.3, 2.0]
        tilings: tilings with a few layers
        return: the encoding for the feature on each layer
        """
        num_dims = len(feature)
        feat_codings = []
        for tiling in self.tilings:
            feat_coding = []
            for i in range(num_dims):
                feat_i = feature[i]
                tiling_i = tiling[i]  # tiling on that dimension
                coding_i = np.digitize(feat_i, tiling_i)
                feat_coding.append(coding_i)
            feat_codings.append(feat_coding)
        return np.array(feat_codings)

    def function_approximation(self, tile_features):
        value = 0
        for t in range(self.number_tilings):
            for x in range(self.bins[0][0]):
                for y in range(self.bins[0][1]):
                    for cell_type in range(3):
                        # print (self.weights[t,cell_type,x,y])
                        # print (tile_features[t,cell_type,x,y])
                        value += self.weights[t,cell_type,x,y]*tile_features[t,cell_type,x,y]
        return value

    def get_q_value(self, state, action, observation):
        s_prime = self.transition_function[state[0]-1][state[1]-1][state[2]][action]
        tile_features = np.zeros((self.number_tilings, 3, self.bins[0][0],self.bins[0][1]))

        for x in range(len(observation)):
            for y in range(len(observation[x])):
                if x != s_prime[0] or y != s_prime[1]:                 
                    if self.data_to_cell_type[observation[x][y]] == CellType.GOOD_FRUIT or self.data_to_cell_type[observation[x][y]] == CellType.BAD_FRUIT or self.data_to_cell_type[observation[x][y]] == CellType.LAVA:
                        if s_prime[2] == SnakeDirection.SOUTH:
                            feature = [x-s_prime[0], y-s_prime[1]]
                        elif s_prime[2] == SnakeDirection.NORTH:
                            feature = [s_prime[0]-x, s_prime[1]-y]
                        elif s_prime[2] == SnakeDirection.EAST:
                            feature = [y-s_prime[1], s_prime[0]-x]
                        elif s_prime[2] == SnakeDirection.WEST:
                            feature = [s_prime[1]-y, x-s_prime[0]]
                        coding = self.get_tile_coding(feature)

                        for t in range(self.number_tilings):
                            tile_features[t, self.data_to_cell_type[observation[x][y]]-1, coding[t][0], coding[t][1]] += 1
        
        q_val = self.curr_reward_map[s_prime[0]][s_prime[1]] + self.discount * self.function_approximation(tile_features)
        return q_val

    def scale(self, X, x_min, x_max):
        nom = (X-X.min())*(x_max-x_min)
        denom = X.max() - X.min()
        denom = denom + (denom == 0)
        return nom/denom + x_min

    def train(self, env, num_episodes=1000, discount=0.95, exploration_range=(1.0, 0.1), exploration_phase_size=0.5, learning_range=(1.0, 0.1), learning_phase_size=0.5):
        max_exploration_rate, min_exploration_rate = exploration_range
        exploration_decay = ((max_exploration_rate - min_exploration_rate) / (num_episodes * exploration_phase_size))
        exploration_rate = max_exploration_rate

        max_learning_rate, min_learning_rate = learning_range
        learning_decay = ((max_learning_rate - min_learning_rate) / (num_episodes * learning_phase_size))
        learning_rate = max_learning_rate

        for episode in range(num_episodes):
            # Reset the environment for the new episode.
            timestep = env.new_episode()
            self.begin_episode()
            game_over = False
            # state = self.get_last_frames(timestep.observation)
            state_ob = timestep.observation

            while not game_over:
                if np.random.random() < exploration_rate:
                    # Explore: take a random action.
                    action = np.random.randint(env.num_actions)
                    self.compute_reward_map(state_ob)
                    self.tile_feature_extraction(state_ob)

                else:
                    # Exploit: take the best known action for this state.
                    action = self.act(state_ob)

                # Act on the environment.
                env.choose_action(action)
                timestep = env.timestep()

                # Remember a new piece of experience.
                reward = timestep.reward
                state_ob_next = timestep.observation
                game_over = timestep.is_episode_end

                tile_features_next = np.zeros((self.number_tilings, 3, self.bins[0][0],self.bins[0][1]))
                state_x_next = 0
                state_y_next = 0

                for x in range(len(state_ob_next)):
                    for y in range(len(state_ob_next[x])):
                        if self.data_to_cell_type[state_ob_next[x][y]] == CellType.SNAKE_HEAD:
                            state_x_next = x
                            state_y_next = y
                            if self.data_to_cell_type[state_ob_next[x-1][y]] == CellType.SNAKE_BODY:
                                state_direction_next = SnakeDirection.SOUTH
                            elif self.data_to_cell_type[state_ob_next[x+1][y]] == CellType.SNAKE_BODY:
                                state_direction_next = SnakeDirection.NORTH
                            elif self.data_to_cell_type[state_ob_next[x][y-1]] == CellType.SNAKE_BODY:
                                state_direction_next =SnakeDirection.EAST
                            elif self.data_to_cell_type[state_ob_next[x][y+1]] == CellType.SNAKE_BODY:
                                state_direction_next = SnakeDirection.WEST
                            else:
                                print("No snake body detected!!!!!") # shouldn't be here
                            
                for x in range(len(state_ob_next)):
                    for y in range(len(state_ob_next[x])):
                        if self.data_to_cell_type[state_ob_next[x][y]] == CellType.GOOD_FRUIT or self.data_to_cell_type[state_ob_next[x][y]] == CellType.BAD_FRUIT or self.data_to_cell_type[state_ob_next[x][y]] == CellType.LAVA:
                            if state_direction_next == SnakeDirection.SOUTH:
                                feature = [x-state_x_next, y-state_y_next]
                            elif state_direction_next == SnakeDirection.NORTH:
                                feature = [state_x_next-x, state_y_next-y]
                            elif state_direction_next == SnakeDirection.EAST:
                                feature = [y-state_y_next, state_x_next-x]
                            elif state_direction_next == SnakeDirection.WEST:
                                feature = [state_y_next-y, x-state_x_next]
                            coding = self.get_tile_coding(feature)

                            for t in range(self.number_tilings):
                                tile_features_next[t, self.data_to_cell_type[state_ob_next[x][y]]-1, coding[t][0], coding[t][1]] += 1

                if game_over:
                    err = reward - self.function_approximation(self.tile_features)
                else:
                    err = reward + discount*self.function_approximation(tile_features_next)-self.function_approximation(self.tile_features)

                for t in range(self.number_tilings):
                    for x in range(self.bins[0][0]):
                        for y in range(self.bins[0][1]):
                            for cell_type in range(3):
                                self.weights[t][cell_type][x][y] += learning_rate*err*self.tile_features[t][cell_type][x][y]

                self.weights = self.scale(self.weights, 0, 1)

                state_ob = state_ob_next
           

            if exploration_rate > min_exploration_rate:
                exploration_rate -= exploration_decay
            if learning_rate > min_learning_rate:
                learning_rate -= learning_decay


            summary = 'Episode {:5d}/{:5d} | Exploration {:.2f} | ' + \
                      'Good Fruits {:2d} | Bad Fruits {:2d} | Lava {:2d} | Timesteps {:4d} | Total Reward {:4d}'
            print(summary.format(
                episode + 1, num_episodes, exploration_rate,
                env.stats.good_fruits_eaten, env.stats.bad_fruits_eaten, env.stats.lava_crossed,
                env.stats.timesteps_survived, env.stats.sum_episode_rewards,
            ))
            
            if episode % 20 == 0 or episode == num_episodes-1:
                weights_file = open(f'tile_coding_weights_'+str(episode)+'.log', 'w')

                for t in range(self.number_tilings):
                    for cell_type in range(3):
                        print('Tiling:'+str(t)+'\n'+'Cell_type:'+str(cell_type)+'\n', file=weights_file)

                        feature_map = '\n'.join([','.join(str(col) for col in row) for row in self.weights[t,cell_type]]) 
                        feature_array = f'{feature_map}\n'
                        print(str(feature_array), file=weights_file)

                weights_file.close()
                
                
    def compute_reward_map(self, observation):
        self.curr_reward_map = []
        state_x = 0
        state_y = 0 
        state_direction = None
        for x in range(len(observation)):
            self.curr_reward_map.append([])
            for y in range(len(observation[x])):
                self.curr_reward_map[-1].append(self.reward_mapping[self.data_to_cell_type[observation[x][y]]])
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
                elif (not self.env_changed) and self.data_to_cell_type[observation[x][y]] != self.data_to_cell_type[self.last_frame[x][y]]:
                    if self.data_to_cell_type[observation[x][y]] != CellType.SNAKE_BODY and self.data_to_cell_type[self.last_frame[x][y]] != CellType.SNAKE_BODY: self.env_changed = True
        
        self.curr_state = [state_x,state_y,state_direction]
        return self.curr_reward_map, 

    def tile_feature_extraction(self, observation):
        self.tile_features = np.zeros((self.number_tilings, 3, self.bins[0][0],self.bins[0][1]))
        for x in range(len(observation)):
            for y in range(len(observation[x])):
                if self.data_to_cell_type[observation[x][y]] == CellType.GOOD_FRUIT or self.data_to_cell_type[observation[x][y]] == CellType.BAD_FRUIT or self.data_to_cell_type[observation[x][y]] == CellType.LAVA:  
                    if self.curr_state[2] == SnakeDirection.SOUTH:
                        feature = [x-self.curr_state[0], y-self.curr_state[1]]
                    elif self.curr_state[2] == SnakeDirection.NORTH:
                        feature = [self.curr_state[0]-x, self.curr_state[1]-y]
                    elif self.curr_state[2] == SnakeDirection.EAST:
                        feature = [y-self.curr_state[1], self.curr_state[0]-x]
                    elif self.curr_state[2] == SnakeDirection.WEST:
                        feature = [self.curr_state[1]-y, x-self.curr_state[0]]
                    coding = self.get_tile_coding(feature)

                    for t in range(self.number_tilings):
                        self.tile_features[t, self.data_to_cell_type[observation[x][y]]-1, coding[t][0], coding[t][1]] += 1
        return self.tile_features

    def act(self, observation, reward=0.0):       
        self.compute_reward_map(observation)
        self.tile_feature_extraction(observation)
        # select action
        selected_action = random.choice(ALL_SNAKE_ACTIONS)
        curr_max_val = -100.0
        for action in ALL_SNAKE_ACTIONS:
            '''s_prime = self.transition_function[state_x-1][state_y-1][state_direction][action]
            peek_reward = self.curr_reward_map[s_prime[0]][s_prime[1]]
            exp_util = peek_reward + self.discount * self.V_estimations[s_prime[0]-1][s_prime[1]-1][s_prime[2]]'''
            exp_util = self.get_q_value(self.curr_state, action, observation)
            if exp_util > curr_max_val:
                curr_max_val = exp_util
                selected_action = action

        self.last_reward = reward
        self.last_frame = observation
        self.env_changed = False
        return selected_action

    def end_episode(self):
        pass

    def initialize_transition_function(self):
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
                        if i == 1:
                            if j < self.grid_size/2: # turn right
                                self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i,j+1,SnakeDirection.EAST)
                            else: # turn left
                                self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i,j-1,SnakeDirection.WEST)
                        if j == 1:
                            if i == 1:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i,j+1,SnakeDirection.EAST)
                            else:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i-1,j,SnakeDirection.NORTH)
                        if j == self.grid_size-2: 
                            if i == 1:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i,j-1,SnakeDirection.WEST)
                            else:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i-1,j,SnakeDirection.NORTH)

                    elif k == SnakeDirection.EAST:
                        self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i,j+1,SnakeDirection.EAST)
                        self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i-1,j,SnakeDirection.NORTH)
                        self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i+1,j,SnakeDirection.SOUTH)
                        if i == 1:
                            if j == self.grid_size-2:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i+1,j,SnakeDirection.SOUTH) # at corner
                            else:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i,j+1,SnakeDirection.EAST)
                        if i == self.grid_size-2:
                            if j == self.grid_size-2:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i-1,j,SnakeDirection.NORTH)
                            else:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i,j+1,SnakeDirection.EAST)
                        if j == self.grid_size-2:
                            if i < self.grid_size/2:
                                self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i+1,j,SnakeDirection.SOUTH)
                            else: # turn left
                                self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i-1,j,SnakeDirection.NORTH)
                            
                    elif k == SnakeDirection.SOUTH:
                        self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i+1,j,SnakeDirection.SOUTH)
                        self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i,j+1,SnakeDirection.EAST)
                        self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i,j-1,SnakeDirection.WEST)
                        if i == self.grid_size-2:
                            if j < self.grid_size/2: # turn right
                                self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i,j+1,SnakeDirection.EAST)
                            else: # turn left
                                self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i,j-1,SnakeDirection.WEST)
                        if j == 1:
                            if i == self.grid_size-2:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i,j+1,SnakeDirection.EAST)
                            else:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i+1,j,SnakeDirection.SOUTH)
                        if j == self.grid_size-2:
                            if i == self.grid_size-2:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i,j-1,SnakeDirection.WEST)
                            else:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i+1,j,SnakeDirection.SOUTH)

                    elif k == SnakeDirection.WEST:
                        self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i,j-1,SnakeDirection.WEST)
                        self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i+1,j,SnakeDirection.SOUTH)
                        self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i-1,j,SnakeDirection.NORTH)  
                        if i == 1:
                            if j == 1:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] =  (i+1,j,SnakeDirection.SOUTH)
                            else:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_RIGHT] = (i,j-1,SnakeDirection.WEST)
                        if i == self.grid_size-2:
                            if j == 1:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i-1,j,SnakeDirection.NORTH) # at corner
                            else:
                                self.transition_function[i-1][j-1][k][SnakeAction.TURN_LEFT] = (i,j-1,SnakeDirection.WEST)
                        if j == 1:                      
                            if i < self.grid_size/2:
                                self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i+1,j,SnakeDirection.SOUTH)
                            else: # turn left
                                self.transition_function[i-1][j-1][k][SnakeAction.MAINTAIN_DIRECTION] = (i-1,j,SnakeDirection.NORTH)
