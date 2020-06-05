import pprint
import random
import time

import numpy as np
import pandas as pd
import threading
from .entities import Snake, Field, CellType, SnakeAction, SnakeDirection, ALL_SNAKE_ACTIONS, SNAKE_GROW, WALL_WARP

PUNISH_WALL = False
PLAY_SOUND = True



class Environment(object):
    """
    Represents the RL environment for the Snake game that implements the game logic,
    provides rewards for the agent and keeps track of game statistics.
    """
    __lock = threading.Lock()
    NUM_INIT = 0
   
    def __deepcopy__(self, memo):
        with Environment.__lock:
            Environment.NUM_INIT += 1
        return self.__init__(self.config,self.stationary,self.verbose)
        
    def __init__(self, config, stationary=False, verbose=2):
        """
        Create a new Snake RL environment.
        
        Args:
            config (dict): level configuration, typically found in JSON configs.  
            verbose (int): verbosity level:
                0 = do not write any debug information;
                1 = write a CSV file containing the statistics for every episode;
                2 = same as 1, but also write a full log file containing the state of each timestep.
        """
        with Environment.__lock:
            Environment.NUM_INIT += 1
        
        self.config = config
        self.initial_config = config['field']
        self.field = Field(level_map=self.initial_config)
        self.snake = None

        self.initial_snake_length = config['initial_snake_length']
        self.rewards = config['rewards']
        self.max_step_limit = config.get('max_step_limit', 1000)
        self.punch = False
        self.is_game_over = False
        self.stationary = stationary
        self.good_fruit_revealed = False
        self.bad_fruit_revealed = False
        self.lava_revealed = False

        self.timestep_index = 0
        self.current_action = None
        self.stats = EpisodeStatistics()
        self.verbose = verbose
        self.debug_file = None
        self.stats_file = None
        self.seed(int(time.time())+Environment.NUM_INIT)

    def seed(self, value):
        """ Initialize the random state of the environment to make results reproducible. """
        random.seed(value)
        np.random.seed(value)
        np.random.RandomState(value)

    @property
    def observation_shape(self):
        """ Get the shape of the state observed at each timestep. """
        return self.field.size, self.field.size

    @property
    def num_actions(self):
        """ Get the number of actions the agent can take. """
        return len(ALL_SNAKE_ACTIONS)

    def new_episode(self):
        """ Reset the environment and begin a new episode. """

        self.field = Field(level_map=self.initial_config)
        self.field.create_level()
        self.stats.reset()
        self.timestep_index = 0

        self.snake = Snake(self.field.find_snake_head(), length=self.initial_snake_length)
        self.field.place_snake(self.snake)

        self.good_fruit, self.bad_fruit, self.lava = self.field.get_initial_items()
        if not self.stationary:
            self.generate_fruit('good', 2)
            self.generate_fruit('bad', 2)
            self.generate_lava(2)
        self.current_action = None
        self.punch = False
        self.punch_wall_pos = [0,0]
        self.is_game_over = False
        self.good_miss_ct = 0 
        self.bad_miss_ct = 0 
        self.lava_miss_ct = 0 

        result = TimestepResult(
            observation=self.get_observation(),
            reward=0,
            is_episode_end=self.is_game_over
        )
        return result


    def get_observation(self):
        """ Observe the state of the environment. """
        return np.copy(self.field._cells)

    def choose_action(self, action):
        """ Choose the action that will be taken at the next timestep. """

        self.current_action = action
        if action == SnakeAction.TURN_LEFT:
            self.snake.turn_left()
        elif action == SnakeAction.TURN_RIGHT:
            self.snake.turn_right()

    def timestep(self, punch_sound=None, good_sound=None, bad_sound=None, very_bad_sound=None):
        """ Execute the timestep and return the new observable state. """

        self.timestep_index += 1
        self.punch = False
        reward = 0

        old_head = self.snake.head
        old_tail = self.snake.tail
        old_mid = self.snake.mid
        next_move = self.snake.peek_next_move()

        # Case for warping
        if WALL_WARP and self.field[next_move] == CellType.WALL:
            self.punch = True
            '''
            if punch_sound and PLAY_SOUND:
                punch_sound.play()
            '''

            x, y = old_head
            next_x, next_y = next_move
            self.punch_wall_pos = next_move

            # North and South
            if abs(next_y - old_head.y) == 1:
            # if (next_y == 0 or next_y == self.field.size - 1):
                # Facing East
                if old_head.x - old_mid.x > 0:                   
                    # Case for a horizontal line or the first half of body being horizontal
                    if old_head.y == old_mid.y:
                        self.snake.direction = SnakeDirection.EAST
                        # Case when snake reaches corner
                        if self.field[self.snake.peek_next_move()] == CellType.WALL:
                            # Find the only feasible direction in corner
                            self.snake.direction = SnakeDirection.SOUTH
                            if self.field[self.snake.peek_next_move()] == CellType.WALL:
                                self.snake.direction = SnakeDirection.NORTH
                                 
                # Facing West
                elif old_head.x- old_mid.x < 0:
                    # Case for a horizontal line or the first half of body being horizontal
                    if old_head.y == old_mid.y:
                        self.snake.direction = SnakeDirection.WEST
                        # Case when snake reaches corner
                        if self.field[self.snake.peek_next_move()] == CellType.WALL:
                            # Find the only feasible direction in corner
                            self.snake.direction = SnakeDirection.SOUTH
                            if self.field[self.snake.peek_next_move()] == CellType.WALL:
                                self.snake.direction = SnakeDirection.NORTH                                                         
                
                # Case for a vertical line or the first half of body being vertical                      
                elif x < self.field.size/2:
                    self.snake.direction = SnakeDirection.EAST
                    if self.field[self.snake.peek_next_move()] == CellType.WALL:
                        self.snake.direction = SnakeDirection.WEST
                else:
                    self.snake.direction = SnakeDirection.WEST
                    if self.field[self.snake.peek_next_move()] == CellType.WALL:
                        self.snake.direction = SnakeDirection.EAST

            # West and East
            elif abs(next_x - old_head.x) == 1:
            # elif (next_x == 0 or next_x == self.field.size - 1):
                # Facing South
                if old_head.y - old_mid.y > 0:                 
                    # Case for a horizontal line or the first half of body being horizontal
                    if old_head.x == old_mid.x:
                        self.snake.direction = SnakeDirection.SOUTH
                        # Case when snake reaches corner
                        if self.field[self.snake.peek_next_move()] == CellType.WALL:
                            # Find the only feasible direction in corner
                            self.snake.direction = SnakeDirection.EAST
                            if self.field[self.snake.peek_next_move()] == CellType.WALL:
                                self.snake.direction = SnakeDirection.WEST
                # Facing North
                elif old_head.y- old_mid.y < 0:
                    # Case for a horizontal line or the first half of body being horizontal
                    if old_head.x == old_mid.x:
                        self.snake.direction = SnakeDirection.NORTH
                        # Case when snake reaches corner
                        if self.field[self.snake.peek_next_move()] == CellType.WALL:
                            # Find the only feasible direction in corner
                            self.snake.direction = SnakeDirection.EAST
                            if self.field[self.snake.peek_next_move()] == CellType.WALL:
                                self.snake.direction = SnakeDirection.WEST                                                
                
                # Case for a vertical line or the first half of body being vertical                      
                elif y < self.field.size/2:
                    self.snake.direction = SnakeDirection.SOUTH
                    if self.field[self.snake.peek_next_move()] == CellType.WALL:
                        self.snake.direction = SnakeDirection.NORTH
                else:
                    self.snake.direction = SnakeDirection.NORTH
                    if self.field[self.snake.peek_next_move()] == CellType.WALL:
                        self.snake.direction = SnakeDirection.SOUTH

            next_move = self.snake.peek_next_move()
            # punish wall crashing behavior ... how to avoid travelling around wall??
            if PUNISH_WALL:
                reward -= 2
        
        if not self.stationary:
            if len(self.good_fruit) < 2:
                self.good_miss_ct += 1
                if self.good_miss_ct >= 3:
                    self.generate_fruit('good', 1)
            else:
                self.good_miss_ct = 0 
                    
            if len(self.bad_fruit) < 2:
                self.bad_miss_ct += 1
                if self.bad_miss_ct >= 3:
                    self.generate_fruit('bad', 1)
            else:
                self.bad_miss_ct = 0 
                    
            if len(self.lava) < 2:
                self.lava_miss_ct += 1
                if self.lava_miss_ct >= 3:
                    self.generate_lava(1)
            else:
                self.lava_miss_ct = 0 

        # Are we about to eat the fruit?
        if next_move in self.good_fruit:
            # Case where snake doesn't grow
            if SNAKE_GROW:
                self.snake.grow()
                old_tail = None
            else:
                self.snake.move()

            if good_sound and PLAY_SOUND:
                good_sound.play()

            #self.generate_fruit('good', 1)
            self.good_fruit.remove(next_move)            
            reward += self.rewards['good_fruit']
            self.stats.good_fruits_eaten += 1

            if self.stationary:
                self.good_fruit_revealed = True

        # About to eat bad fruit
        elif next_move in self.bad_fruit:
            self.snake.move()

            if bad_sound and PLAY_SOUND:
                bad_sound.play()

            #self.generate_fruit('bad', 1) 
            self.bad_fruit.remove(next_move)           
            reward += self.rewards['bad_fruit']
            self.stats.bad_fruits_eaten += 1

            if self.stationary:
                self.bad_fruit_revealed = True

         # About to cross lava
        elif next_move in self.lava:
            self.snake.move()

            if very_bad_sound and PLAY_SOUND:
                very_bad_sound.play()

            #self.generate_lava(1) 
            self.lava.remove(next_move)          
            reward += self.rewards['lava']
            self.stats.lava_crossed += 1

            if self.stationary:
                self.lava_revealed = True

        # If not, just move forward.
        else:
            self.snake.move()
            reward += self.rewards['timestep']

        self.field.update_snake_footprint(old_head, old_tail, self.snake.head)

        # Hit a wall or own body?
        if not self.is_alive():
            if self.has_hit_wall():
                self.stats.termination_reason = 'hit_wall'   
            if self.has_hit_own_body():
                self.stats.termination_reason = 'hit_own_body'
            self.field[self.snake.head] = CellType.SNAKE_HEAD
            #self.is_game_over = True
            reward = self.rewards['died']

        # Stationary environment? (terminates when reaches an item)
        if self.stationary:
            if reward != 0:
                self.is_game_over = True
                self.stats.termination_reason = 'successfully reached an item'

        # Exceeded the limit of moves?
        if self.timestep_index >= self.max_step_limit:
            self.is_game_over = True
            self.stats.termination_reason = 'timestep_limit_exceeded'

        result = TimestepResult(
            observation=self.get_observation(),
            reward=reward,
            is_episode_end=self.is_game_over
        )
        
        return result

    def generate_fruit(self, type, num, position=None):
        """ Generate a new fruit at a random unoccupied cell. """
        if type == 'good':
            fruitType = CellType.GOOD_FRUIT
        elif type == 'bad':
            fruitType = CellType.BAD_FRUIT

        if position is None:
            position = []
            for i in range(0, num):
                spot = self.field.get_random_empty_cell()
                self.field[spot] = fruitType
                position.append(spot)        
        else:        
            for spot in position:
                self.field[spot] = fruitType

        if type == 'good':
            self.good_fruit = self.good_fruit + position
        elif type == 'bad':
            self.bad_fruit = self.bad_fruit + position
        
    def generate_lava(self, num, position=None):
        """ Generate a new lava at a random unoccupied cell. """
        if position is None:
            position = []
            for i in range(0, num):
                spot = self.field.get_random_empty_cell()
                self.field[spot] = CellType.LAVA
                position.append(spot)        
        else:        
            for spot in position:
                self.field[spot] = CellType.LAVA

        self.lava = self.lava + position

    def has_hit_wall(self):
        """ True if the snake has hit a wall, False otherwise. """
        return self.field[self.snake.head] == CellType.WALL

    def has_hit_own_body(self):
        """ True if the snake has hit its own body, False otherwise. """
        return self.field[self.snake.head] == CellType.SNAKE_BODY

    def is_alive(self):
        """ True if the snake is still alive, False otherwise. """
        return not self.has_hit_wall() and not self.has_hit_own_body()


class TimestepResult(object):
    """ Represents the information provided to the agent after each timestep. """

    def __init__(self, observation, reward, is_episode_end):
        self.observation = observation
        self.reward = reward
        self.is_episode_end = is_episode_end

    def __str__(self):
        field_map = '\n'.join([
            ''.join(str(cell) for cell in row)
            for row in self.observation
        ])
        return f'{field_map}\nR={self.reward}\nend={self.is_episode_end}\n'


class EpisodeStatistics(object):
    """ Represents the summary of the agent's performance during the episode. """

    def __init__(self):
        self.reset()

    def reset(self):
        """ Forget all previous statistics and prepare for a new episode. """
        self.timesteps_survived = 0
        self.sum_episode_rewards = 0
        self.good_fruits_eaten = 0
        self.bad_fruits_eaten = 0
        self.lava_crossed = 0
        self.termination_reason = None
        self.action_counter = {
            action: 0
            for action in ALL_SNAKE_ACTIONS
        }


    def record_timestep(self, action, result):
        """ Update the stats based on the current timestep results. """
        self.sum_episode_rewards += result.reward
        if action is not None:
            self.action_counter[int(action)] += 1

    def flatten(self):
        """ Format all episode statistics as a flat object. """
        flat_stats = {
            'timesteps_survived': self.timesteps_survived,
            'sum_episode_rewards': self.sum_episode_rewards,
            'mean_reward': self.sum_episode_rewards / self.timesteps_survived if self.timesteps_survived else None,
            'good_fruits_eaten': self.good_fruits_eaten,
            'bad_fruits_eaten': self.bad_fruits_eaten,
            'lava_crossed': self.lava_crossed,
            'termination_reason': self.termination_reason,
        }
        flat_stats.update({
            f'action_counter_{action}': self.action_counter.get(action, 0)
            for action in ALL_SNAKE_ACTIONS
        })
        return flat_stats

    def to_dataframe(self):
        """ Convert the episode statistics to a Pandas data frame. """
        return pd.DataFrame([self.flatten()])

    def __str__(self):
        return pprint.pformat(self.flatten())
