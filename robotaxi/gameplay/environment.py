import pprint
import random
import time

import numpy as np
import pandas as pd

from .entities import Snake, Field, CellType, SnakeAction, SnakeDirection, ALL_SNAKE_ACTIONS, SNAKE_GROW, WALL_WARP

PUNISH_WALL = False
PLAY_SOUND = True

class Environment(object):
    """
    Represents the RL environment for the Snake game that implements the game logic,
    provides rewards for the agent and keeps track of game statistics.
    """

    def __init__(self, config, stationary=False, collaboration=False, verbose=2, participant=None):
        """
        Create a new Snake RL environment.
        
        Args:
            config (dict): level configuration, typically found in JSON configs.  
            verbose (int): verbosity level:
                0 = do not write any debug information;
                1 = write a CSV file containing the statistics for every episode;
                2 = same as 1, but also write a full log file containing the state of each timestep.
        """
        self.config = config
        self.initial_config = config['field']
        self.field = Field(level_map=self.initial_config)
        self.snake = None
        self.collaborator = None
        self.collaboration = collaboration
        self.in_pit = False
        self.original_direction = SnakeDirection.NORTH

        self.initial_snake_length = config['initial_snake_length']
        self.rewards = config['rewards']
        self.max_step_limit = config.get('max_step_limit', 100)
        self.punch = False
        self.punch_collaborator = False
        self.is_game_over = False
        self.stationary = stationary
        self.good_fruit_revealed = False
        self.bad_fruit_revealed = False
        self.lava_revealed = False
        self.good_fruit_num = 2
        self.bad_fruit_num = 2 if not self.collaboration else 0
        self.lava_num = 2

        self.timestep_index = 0
        self.current_action = None
        self.current_action_collaborator = None
        self.stats = EpisodeStatistics()
        self.stats_collaborator = EpisodeStatistics()
        self.verbose = verbose
        self.debug_file = None
        self.stats_file = None
        self.stats_file_collaborator = None
        self.debug_file_collaborator = None
        self.participant = participant

    def update_field(self, config):
        self.initial_config = config['field']
        self.field = Field(level_map=self.initial_config)
    
    def new_episode_with_field(self, field):

        self.field = field
        self.field.create_level(init_cells=False)
        self.stats.reset()
        self.timestep_index = 0        
        self.snake = Snake(self.field.find_snake_head(), length=self.initial_snake_length, body_coord=self.field.find_snake_body())        

        self.good_fruit, self.bad_fruit, self.lava, self.pit = self.field.get_initial_items()
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

        self.record_timestep_stats(result)
        return result
       
    def seed(self, value):
        """ Initialize the random state of the environment to make results reproducible. """
        random.seed(value)
        np.random.seed(value)

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

        self.seed(random.randint(12345,99999))
        self.field = Field(level_map=self.initial_config)
        self.field.create_level()
        
        self.stats.reset()
        self.timestep_index = 0

        self.snake = Snake(self.field.find_snake_head(), length=self.initial_snake_length)
        self.field.place_snake(self.snake)

        if self.collaboration:
            self.collaborator = Snake(self.field.find_collaborator(), length=self.initial_snake_length)
            self.field.place_collaborator(self.collaborator)

        self.good_fruit, self.bad_fruit, self.lava, self.pit = self.field.get_initial_items()
        if not self.stationary:
            self.generate_fruit('good', self.good_fruit_num)
            self.generate_fruit('bad', self.bad_fruit_num)
            self.generate_lava(self.lava_num)
        self.current_action = None
        self.punch = False
        self.punch_collaborator = False
        self.punch_wall_pos = [0,0]
        self.punch_wall_pos_collaborator = [0,0]
        self.is_game_over = False
        self.good_miss_ct = 0 
        self.bad_miss_ct = 0 
        self.lava_miss_ct = 0 

        result = TimestepResult(
            observation=self.get_observation(),
            reward=0,
            is_episode_end=self.is_game_over
        )

        self.record_timestep_stats(result)
        if self.collaboration:
            self.record_timestep_stats_collaborator(result)
        return result

    def record_timestep_stats(self, result, agent_mode=0):
        """ Record environment statistics according to the verbosity level. """
        timestamp = time.strftime('%Y%m%d-%H%M%S')

        # Write CSV header for the stats file.
        if self.verbose >= 1 and self.stats_file is None:
            if self.participant is None: self.stats_file = open(f'csv/autocar_{self.field.size}_{timestamp}.csv', 'w')
            else: self.stats_file = open(f'csv/autocar_{self.field.size}_{self.participant}_{timestamp}.csv', 'w')
            stats_csv_header_line = self.stats.to_dataframe()[:0].to_csv(index=None)
            print(stats_csv_header_line, file=self.stats_file, end='', flush=True)

        # Create a blank debug log file.
        if self.verbose >= 2 and self.debug_file is None:
            if self.participant is None: self.debug_file = open(f'log/autocar_{self.field.size}_{timestamp}.log', 'w')
            else: self.debug_file = open(f'log/autocar_{self.field.size}_{self.participant}_{timestamp}.log', 'w')            
            print('max_step_limit:'+str(self.max_step_limit)+'\n', file=self.debug_file)

        self.stats.record_timestep(self.current_action, result)
        self.stats.timesteps_survived = self.timestep_index

        if self.verbose >= 2:
            print(str(result)+'punch:'+str(self.punch)+'\npwall_pos:'+str(self.punch_wall_pos)+'\ndirection:('+str(self.snake.direction[0])+','+str(self.snake.direction[1])+')\nAgent:' + str(agent_mode) + '\n', file=self.debug_file)

        # Log episode stats if the appropriate verbosity level is set.
        if result.is_episode_end:
            if self.verbose >= 1:
                stats_csv_line = self.stats.to_dataframe().to_csv(header=False, index=None)
                print(stats_csv_line, file=self.stats_file, end='', flush=True)
            if self.verbose >= 2:
                print(self.stats, file=self.debug_file)

    def record_timestep_stats_collaborator(self, result, agent_mode=0):
        """ Record environment statistics according to the verbosity level. """
        timestamp = time.strftime('%Y%m%d-%H%M%S')

        # Write CSV header for the stats file.
        if self.verbose >= 1 and self.stats_file_collaborator is None:
            self.stats_file_collaborator = open(f'csv/autocar_collaborator_{self.field.size}_{timestamp}.csv', 'w')
            stats_csv_header_line = self.stats_collaborator.to_dataframe()[:0].to_csv(index=None)
            print(stats_csv_header_line, file=self.stats_file_collaborator, end='', flush=True)

        # Create a blank debug log file.
        if self.verbose >= 2 and self.debug_file_collaborator is None:
            self.debug_file_collaborator = open(f'log/autocar_collaborator_{self.field.size}_{timestamp}.log', 'w')
            print('max_step_limit:'+str(self.max_step_limit)+'\n', file=self.debug_file_collaborator)

        self.stats_collaborator.record_timestep(self.current_action_collaborator, result)
        self.stats_collaborator.timesteps_survived = self.timestep_index

        if self.verbose >= 2:
            print(str(result)+'punch:'+str(self.punch_collaborator)+'\npwall_pos:'+str(self.punch_wall_pos_collaborator)+'\ndirection:('+str(self.collaborator.direction[0])+','+str(self.collaborator.direction[1])+')\nAgent:' + str(agent_mode) + '\n', file=self.debug_file_collaborator)

        # Log episode stats if the appropriate verbosity level is set.
        if result.is_episode_end:
            if self.verbose >= 1:
                stats_csv_line = self.stats_collaborator.to_dataframe().to_csv(header=False, index=None)
                print(stats_csv_line, file=self.stats_file_collaborator, end='', flush=True)
            if self.verbose >= 2:
                print(self.stats_collaborator, file=self.debug_file_collaborator)
                

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

    def choose_action_collaborator(self, action):
        """ Choose the action that will be taken at the next timestep. """
        self.current_action_collaborator = action
        if action == SnakeAction.TURN_LEFT:
            self.collaborator.turn_left()
        elif action == SnakeAction.TURN_RIGHT:
            self.collaborator.turn_right()

    def timestep(self, punch_sound=None, good_sound=None, bad_sound=None, very_bad_sound=None, free_sound=None, agent_mode=0):
        """ Execute the timestep and return the new observable state. """

        self.timestep_index += 1
        self.punch = False
        reward = 0
        wall_types = [CellType.WALL, CellType.COLLABORATOR_HEAD]

        old_head = self.snake.head
        old_tail = self.snake.tail
        old_mid = self.snake.mid
        next_move = self.snake.peek_next_move()

        # Unlock the collaborator
        if self.collaborator is not None:
            if next_move.x == self.collaborator.head.x and next_move.y == self.collaborator.head.y:
                if free_sound and PLAY_SOUND and self.in_pit:
                    free_sound.play()
                self.in_pit = False

        # Case for warping
        if WALL_WARP and self.field[next_move] in wall_types:
            self.punch = True

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
                        if self.field[self.snake.peek_next_move()] in wall_types:
                            # Find the only feasible direction in corner
                            self.snake.direction = SnakeDirection.SOUTH
                            if self.field[self.snake.peek_next_move()] in wall_types:
                                self.snake.direction = SnakeDirection.NORTH
                                 
                # Facing West
                elif old_head.x- old_mid.x < 0:
                    # Case for a horizontal line or the first half of body being horizontal
                    if old_head.y == old_mid.y:
                        self.snake.direction = SnakeDirection.WEST
                        # Case when snake reaches corner
                        if self.field[self.snake.peek_next_move()] in wall_types:
                            # Find the only feasible direction in corner
                            self.snake.direction = SnakeDirection.SOUTH
                            if self.field[self.snake.peek_next_move()] in wall_types:
                                self.snake.direction = SnakeDirection.NORTH                                                         
                
                # Case for a vertical line or the first half of body being vertical                      
                elif x < self.field.size/2:
                    self.snake.direction = SnakeDirection.EAST
                    if self.field[self.snake.peek_next_move()] in wall_types:
                        self.snake.direction = SnakeDirection.WEST
                else:
                    self.snake.direction = SnakeDirection.WEST
                    if self.field[self.snake.peek_next_move()] in wall_types:
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
                        if self.field[self.snake.peek_next_move()] in wall_types:
                            # Find the only feasible direction in corner
                            self.snake.direction = SnakeDirection.EAST
                            if self.field[self.snake.peek_next_move()] in wall_types:
                                self.snake.direction = SnakeDirection.WEST
                # Facing North
                elif old_head.y- old_mid.y < 0:
                    # Case for a horizontal line or the first half of body being horizontal
                    if old_head.x == old_mid.x:
                        self.snake.direction = SnakeDirection.NORTH
                        # Case when snake reaches corner
                        if self.field[self.snake.peek_next_move()] in wall_types:
                            # Find the only feasible direction in corner
                            self.snake.direction = SnakeDirection.EAST
                            if self.field[self.snake.peek_next_move()] in wall_types:
                                self.snake.direction = SnakeDirection.WEST                                                
                
                # Case for a vertical line or the first half of body being vertical                      
                elif y < self.field.size/2:
                    self.snake.direction = SnakeDirection.SOUTH
                    if self.field[self.snake.peek_next_move()] in wall_types:
                        self.snake.direction = SnakeDirection.NORTH
                else:
                    self.snake.direction = SnakeDirection.NORTH
                    if self.field[self.snake.peek_next_move()] in wall_types:
                        self.snake.direction = SnakeDirection.SOUTH

            next_move = self.snake.peek_next_move()
            # punish wall crashing behavior ... how to avoid travelling around wall??
            if PUNISH_WALL:
                reward -= 2
        
        if not self.stationary:
            if not self.in_pit:
                if len(self.good_fruit) < self.good_fruit_num:
                    self.good_miss_ct += 1
                    if self.good_miss_ct >= 3:
                        self.generate_fruit('good', 1)
                else:
                    self.good_miss_ct = 0
                    
            if len(self.bad_fruit) < self.bad_fruit_num:
                self.bad_miss_ct += 1
                if self.bad_miss_ct >= 3:
                    self.generate_fruit('bad', 1)
            else:
                self.bad_miss_ct = 0 
                    
            if len(self.lava) < self.lava_num:
                self.lava_miss_ct += 1
                if self.lava_miss_ct >= 3:
                    self.generate_lava(1)
            else:
                self.lava_miss_ct = 0 

        # Are we about to eat the fruit?
        if next_move in self.good_fruit:
            # Case where snake doesn't grow
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

        if self.collaboration: 
            self.field.update_snake_footprint(old_head, old_tail, self.snake.head, self.collaborator.head, self.collaborator.tail)
        else:
            self.field.update_snake_footprint(old_head, old_tail, self.snake.head)

        # Hit a wall or own body?
        if not self.is_alive():
            if self.has_hit_wall():
                self.stats.termination_reason = 'hit_wall'   
            if self.has_hit_own_body():
                self.stats.termination_reason = 'hit_own_body'
            self.field[self.snake.head] = CellType.SNAKE_HEAD
            self.is_game_over = True
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
        self.record_timestep_stats(result, agent_mode)
        return result

    def timestep_collaborator(self, punch_sound=None, good_sound=None, bad_sound=None, very_bad_sound=None, stuck_sound=None, agent_mode=0):
        """ Execute the timestep and return the new observable state. """

        self.punch_collaborator = False
        reward = 0
        wall_types = [CellType.WALL, CellType.SNAKE_HEAD]

        old_head = self.collaborator.head
        old_tail = self.collaborator.tail
        old_mid = self.collaborator.mid
        next_move = self.collaborator.peek_next_move()
        stuck = self.in_pit

        # Case for warping
        if WALL_WARP and self.field[next_move] in wall_types:
            self.punch_collaborator = True
            x, y = old_head
            next_x, next_y = next_move
            self.punch_wall_pos_collaborator = next_move

            # North and South
            if abs(next_y - old_head.y) == 1:
            # if (next_y == 0 or next_y == self.field.size - 1):
                # Facing East
                if old_head.x - old_mid.x > 0:                   
                    # Case for a horizontal line or the first half of body being horizontal
                    if old_head.y == old_mid.y:
                        self.collaborator.direction = SnakeDirection.EAST
                        # Case when snake reaches corner
                        if self.field[self.collaborator.peek_next_move()] in wall_types:
                            # Find the only feasible direction in corner
                            self.collaborator.direction = SnakeDirection.SOUTH
                            if self.field[self.collaborator.peek_next_move()] in wall_types:
                                self.collaborator.direction = SnakeDirection.NORTH
                                 
                # Facing West
                elif old_head.x- old_mid.x < 0:
                    # Case for a horizontal line or the first half of body being horizontal
                    if old_head.y == old_mid.y:
                        self.collaborator.direction = SnakeDirection.WEST
                        # Case when snake reaches corner
                        if self.field[self.collaborator.peek_next_move()] in wall_types:
                            # Find the only feasible direction in corner
                            self.collaborator.direction = SnakeDirection.SOUTH
                            if self.field[self.collaborator.peek_next_move()] in wall_types:
                                self.collaborator.direction = SnakeDirection.NORTH                                                         
                
                # Case for a vertical line or the first half of body being vertical                      
                elif x < self.field.size/2:
                    self.collaborator.direction = SnakeDirection.EAST
                    if self.field[self.collaborator.peek_next_move()] in wall_types:
                        self.collaborator.direction = SnakeDirection.WEST
                else:
                    self.collaborator.direction = SnakeDirection.WEST
                    if self.field[self.collaborator.peek_next_move()] in wall_types:
                        self.collaborator.direction = SnakeDirection.EAST

            # West and East
            elif abs(next_x - old_head.x) == 1:
            # elif (next_x == 0 or next_x == self.field.size - 1):
                # Facing South
                if old_head.y - old_mid.y > 0:                 
                    # Case for a horizontal line or the first half of body being horizontal
                    if old_head.x == old_mid.x:
                        self.collaborator.direction = SnakeDirection.SOUTH
                        # Case when snake reaches corner
                        if self.field[self.collaborator.peek_next_move()] in wall_types:
                            # Find the only feasible direction in corner
                            self.collaborator.direction = SnakeDirection.EAST
                            if self.field[self.collaborator.peek_next_move()] in wall_types:
                                self.collaborator.direction = SnakeDirection.WEST
                # Facing North
                elif old_head.y- old_mid.y < 0:
                    # Case for a horizontal line or the first half of body being horizontal
                    if old_head.x == old_mid.x:
                        self.collaborator.direction = SnakeDirection.NORTH
                        # Case when snake reaches corner
                        if self.field[self.collaborator.peek_next_move()] in wall_types:
                            # Find the only feasible direction in corner
                            self.collaborator.direction = SnakeDirection.EAST
                            if self.field[self.collaborator.peek_next_move()] in wall_types:
                                self.collaborator.direction = SnakeDirection.WEST                                                
                
                # Case for a vertical line or the first half of body being vertical                      
                elif y < self.field.size/2:
                    self.collaborator.direction = SnakeDirection.SOUTH
                    if self.field[self.collaborator.peek_next_move()] in wall_types:
                        self.collaborator.direction = SnakeDirection.NORTH
                else:
                    self.collaborator.direction = SnakeDirection.NORTH
                    if self.field[self.collaborator.peek_next_move()] in wall_types:
                        self.collaborator.direction = SnakeDirection.SOUTH

            next_move = self.collaborator.peek_next_move()
            # punish wall crashing behavior ... how to avoid travelling around wall??
            if PUNISH_WALL:
                reward -= 2 

        # Case for collaborator trapped in pit
        if self.in_pit:
            next_move = old_head
            self.collaborator.direction = self.original_direction

        # Are we about to eat the fruit?
        if next_move in self.good_fruit:
            # Case where snake doesn't grow
            if SNAKE_GROW:
                self.collaborator.grow()
                old_tail = None
            else:
                self.collaborator.move()

            if punch_sound and PLAY_SOUND:
                punch_sound.play()

            #self.generate_fruit('good', 1)
            self.good_fruit.remove(next_move)            
            reward += self.rewards['lava']
            self.stats_collaborator.good_fruits_eaten += 1

            if self.stationary:
                self.good_fruit_revealed = True

        # About to eat bad fruit
        elif next_move in self.bad_fruit:
            self.collaborator.move()

            if bad_sound and PLAY_SOUND:
                bad_sound.play()

            #self.generate_fruit('bad', 1) 
            self.bad_fruit.remove(next_move)           
            reward += self.rewards['bad_fruit']
            self.stats_collaborator.bad_fruits_eaten += 1

            if self.stationary:
                self.bad_fruit_revealed = True

         # About to cross lava
        elif next_move in self.lava:
            self.collaborator.move()

            if very_bad_sound and PLAY_SOUND:
                good_sound.play()
            #    very_bad_sound.play()

            #self.generate_lava(1) 
            self.lava.remove(next_move)          
            reward += self.rewards['good_fruit']
            self.stats_collaborator.lava_crossed += 1

            if self.stationary:
                self.lava_revealed = True

        elif next_move in self.pit:
            if not self.in_pit:
                self.collaborator.move()
                self.original_direction = self.collaborator.direction
                #if stuck_sound and PLAY_SOUND:
                #    stuck_sound.play()
            else:
                stuck = True
            reward += self.rewards['timestep']
            self.in_pit = True

        # If not, just move forward.
        else:
            self.collaborator.move()
            reward += self.rewards['timestep']

        if not stuck:
            self.field.update_collaborator_footprint(old_head, old_tail, self.collaborator.head)
        else:
            if stuck_sound and PLAY_SOUND:
                stuck_sound.play()
        # Hit a wall or own body?
        if not self.is_alive(self.collaborator):
            if self.has_hit_wall(self.collaborator):
                self.stats_collaborator.termination_reason = 'hit_wall'   
            if self.has_hit_own_body(self.collaborator):
                self.stats_collaborator.termination_reason = 'hit_own_body'
            self.field[self.collaborator.head] = CellType.SNAKE_HEAD
            self.is_game_over = True
            reward = self.rewards['died']

        # Stationary environment? (terminates when reaches an item)
        if self.stationary:
            if reward != 0:
                self.is_game_over = True
                self.stats_collaborator.termination_reason = 'successfully reached an item'

        # Exceeded the limit of moves?
        if self.timestep_index >= self.max_step_limit:
            self.is_game_over = True
            self.stats_collaborator.termination_reason = 'timestep_limit_exceeded'

        result = TimestepResult(
            observation=self.get_observation(),
            reward=reward,
            is_episode_end=self.is_game_over
        )
        self.record_timestep_stats_collaborator(result, agent_mode)
        return result

    def timestep_team(self, punch_sound=None, good_sound=None, bad_sound=None, very_bad_sound=None, stuck_sound=None, free_sound=None, agent_mode=0):
        """ Execute the timestep and return the new observable state. """

        self.timestep_index += 1
        self.punch = False
        reward = 0
        wall_types = [CellType.WALL, CellType.COLLABORATOR_HEAD]

        old_head = self.snake.head
        old_tail = self.snake.tail
        old_mid = self.snake.mid
        next_move = self.snake.peek_next_move()
        
        self.punch_collaborator = False
        reward_collaborator = 0
        wall_types_collaborator = [CellType.WALL, CellType.SNAKE_HEAD]

        old_head_collaborator = self.collaborator.head
        old_tail_collaborator = self.collaborator.tail
        old_mid_collaborator = self.collaborator.mid
        next_move_collaborator = self.collaborator.peek_next_move()
        stuck = self.in_pit

        # Unlock the collaborator
        if self.collaborator is not None:
            if next_move.x == self.collaborator.head.x and next_move.y == self.collaborator.head.y:
                if free_sound and PLAY_SOUND and self.in_pit:
                    free_sound.play()
                self.in_pit = False

        # Case for warping
        if WALL_WARP and self.field[next_move] in wall_types:
            self.punch = True

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
                        if self.field[self.snake.peek_next_move()] in wall_types:
                            # Find the only feasible direction in corner
                            self.snake.direction = SnakeDirection.SOUTH
                            if self.field[self.snake.peek_next_move()] in wall_types:
                                self.snake.direction = SnakeDirection.NORTH
                                 
                # Facing West
                elif old_head.x- old_mid.x < 0:
                    # Case for a horizontal line or the first half of body being horizontal
                    if old_head.y == old_mid.y:
                        self.snake.direction = SnakeDirection.WEST
                        # Case when snake reaches corner
                        if self.field[self.snake.peek_next_move()] in wall_types:
                            # Find the only feasible direction in corner
                            self.snake.direction = SnakeDirection.SOUTH
                            if self.field[self.snake.peek_next_move()] in wall_types:
                                self.snake.direction = SnakeDirection.NORTH                                                         
                
                # Case for a vertical line or the first half of body being vertical                      
                elif x < self.field.size/2:
                    self.snake.direction = SnakeDirection.EAST
                    if self.field[self.snake.peek_next_move()] in wall_types:
                        self.snake.direction = SnakeDirection.WEST
                else:
                    self.snake.direction = SnakeDirection.WEST
                    if self.field[self.snake.peek_next_move()] in wall_types:
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
                        if self.field[self.snake.peek_next_move()] in wall_types:
                            # Find the only feasible direction in corner
                            self.snake.direction = SnakeDirection.EAST
                            if self.field[self.snake.peek_next_move()] in wall_types:
                                self.snake.direction = SnakeDirection.WEST
                # Facing North
                elif old_head.y- old_mid.y < 0:
                    # Case for a horizontal line or the first half of body being horizontal
                    if old_head.x == old_mid.x:
                        self.snake.direction = SnakeDirection.NORTH
                        # Case when snake reaches corner
                        if self.field[self.snake.peek_next_move()] in wall_types:
                            # Find the only feasible direction in corner
                            self.snake.direction = SnakeDirection.EAST
                            if self.field[self.snake.peek_next_move()] in wall_types:
                                self.snake.direction = SnakeDirection.WEST                                                
                
                # Case for a vertical line or the first half of body being vertical                      
                elif y < self.field.size/2:
                    self.snake.direction = SnakeDirection.SOUTH
                    if self.field[self.snake.peek_next_move()] in wall_types:
                        self.snake.direction = SnakeDirection.NORTH
                else:
                    self.snake.direction = SnakeDirection.NORTH
                    if self.field[self.snake.peek_next_move()] in wall_types:
                        self.snake.direction = SnakeDirection.SOUTH

            next_move = self.snake.peek_next_move()
            # punish wall crashing behavior ... how to avoid travelling around wall??
            if PUNISH_WALL:
                reward -= 2
        
        
        # Case for warping collaborator
        if WALL_WARP and self.field[next_move_collaborator] in wall_types_collaborator:
            self.punch_collaborator = True
            x_collaborator, y_collaborator = old_head_collaborator
            next_x_collaborator, next_y_collaborator = next_move_collaborator
            self.punch_wall_pos_collaborator = next_move_collaborator

            # North and South
            if abs(next_y_collaborator - old_head_collaborator.y) == 1:
            # if (next_y == 0 or next_y == self.field.size - 1):
                # Facing East
                if old_head_collaborator.x - old_mid_collaborator.x > 0:                   
                    # Case for a horizontal line or the first half of body being horizontal
                    if old_head_collaborator.y == old_mid_collaborator.y:
                        self.collaborator.direction = SnakeDirection.EAST
                        # Case when snake reaches corner
                        if self.field[self.collaborator.peek_next_move()] in wall_types_collaborator:
                            # Find the only feasible direction in corner
                            self.collaborator.direction = SnakeDirection.SOUTH
                            if self.field[self.collaborator.peek_next_move()] in wall_types_collaborator:
                                self.collaborator.direction = SnakeDirection.NORTH
                                 
                # Facing West
                elif old_head_collaborator.x- old_mid_collaborator.x < 0:
                    # Case for a horizontal line or the first half of body being horizontal
                    if old_head_collaborator.y == old_mid_collaborator.y:
                        self.collaborator.direction = SnakeDirection.WEST
                        # Case when snake reaches corner
                        if self.field[self.collaborator.peek_next_move()] in wall_types_collaborator:
                            # Find the only feasible direction in corner
                            self.collaborator.direction = SnakeDirection.SOUTH
                            if self.field[self.collaborator.peek_next_move()] in wall_types_collaborator:
                                self.collaborator.direction = SnakeDirection.NORTH                                                         
                
                # Case for a vertical line or the first half of body being vertical                      
                elif x_collaborator < self.field.size/2:
                    self.collaborator.direction = SnakeDirection.EAST
                    if self.field[self.collaborator.peek_next_move()] in wall_types_collaborator:
                        self.collaborator.direction = SnakeDirection.WEST
                else:
                    self.collaborator.direction = SnakeDirection.WEST
                    if self.field[self.collaborator.peek_next_move()] in wall_types_collaborator:
                        self.collaborator.direction = SnakeDirection.EAST

            # West and East
            elif abs(next_x_collaborator - old_head_collaborator.x) == 1:
            # elif (next_x == 0 or next_x == self.field.size - 1):
                # Facing South
                if old_head_collaborator.y - old_mid_collaborator.y > 0:                 
                    # Case for a horizontal line or the first half of body being horizontal
                    if old_head_collaborator.x == old_mid_collaborator.x:
                        self.collaborator.direction = SnakeDirection.SOUTH
                        # Case when snake reaches corner
                        if self.field[self.collaborator.peek_next_move()] in wall_types_collaborator:
                            # Find the only feasible direction in corner
                            self.collaborator.direction = SnakeDirection.EAST
                            if self.field[self.collaborator.peek_next_move()] in wall_types_collaborator:
                                self.collaborator.direction = SnakeDirection.WEST
                # Facing North
                elif old_head_collaborator.y- old_mid_collaborator.y < 0:
                    # Case for a horizontal line or the first half of body being horizontal
                    if old_head_collaborator.x == old_mid_collaborator.x:
                        self.collaborator.direction = SnakeDirection.NORTH
                        # Case when snake reaches corner
                        if self.field[self.collaborator.peek_next_move()] in wall_types_collaborator:
                            # Find the only feasible direction in corner
                            self.collaborator.direction = SnakeDirection.EAST
                            if self.field[self.collaborator.peek_next_move()] in wall_types_collaborator:
                                self.collaborator.direction = SnakeDirection.WEST                                                
                
                # Case for a vertical line or the first half of body being vertical                      
                elif y_collaborator < self.field.size/2:
                    self.collaborator.direction = SnakeDirection.SOUTH
                    if self.field[self.collaborator.peek_next_move()] in wall_types_collaborator:
                        self.collaborator.direction = SnakeDirection.NORTH
                else:
                    self.collaborator.direction = SnakeDirection.NORTH
                    if self.field[self.collaborator.peek_next_move()] in wall_types_collaborator:
                        self.collaborator.direction = SnakeDirection.SOUTH

            next_move_collaborator = self.collaborator.peek_next_move()
            # punish wall crashing behavior ... how to avoid travelling around wall??
            if PUNISH_WALL:
                reward_collaborator -= 2
        
        
        # Case for collaborator trapped in pit
        if self.in_pit:
            next_move_collaborator = old_head_collaborator
            self.collaborator.direction = self.original_direction
        
        
        if not self.stationary:
            if not self.in_pit:
                if len(self.good_fruit) < self.good_fruit_num:
                    self.good_miss_ct += 1
                    if self.good_miss_ct >= 3:
                        self.generate_fruit('good', 1)
                else:
                    self.good_miss_ct = 0
                    
            if len(self.bad_fruit) < self.bad_fruit_num:
                self.bad_miss_ct += 1
                if self.bad_miss_ct >= 3:
                    self.generate_fruit('bad', 1)
            else:
                self.bad_miss_ct = 0 
                    
            if len(self.lava) < self.lava_num:
                self.lava_miss_ct += 1
                if self.lava_miss_ct >= 3:
                    self.generate_lava(1)
            else:
                self.lava_miss_ct = 0 

        # Are we about to eat the fruit?
        if next_move in self.good_fruit:
            # Case where snake doesn't grow
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
        
        
        # Is collaborator about to eat the fruit?
        if next_move_collaborator in self.good_fruit:
            # Case where snake doesn't grow
            if SNAKE_GROW:
                self.collaborator.grow()
                old_tail_collaborator = None
            else:
                self.collaborator.move()

            if punch_sound and PLAY_SOUND:
                punch_sound.play()

            #self.generate_fruit('good', 1)
            self.good_fruit.remove(next_move_collaborator)            
            reward_collaborator += self.rewards['lava']
            self.stats_collaborator.good_fruits_eaten += 1

            if self.stationary:
                self.good_fruit_revealed = True

        # About to eat bad fruit
        elif next_move_collaborator in self.bad_fruit:
            self.collaborator.move()

            if bad_sound and PLAY_SOUND:
                bad_sound.play()

            #self.generate_fruit('bad', 1) 
            self.bad_fruit.remove(next_move_collaborator)           
            reward_collaborator += self.rewards['bad_fruit']
            self.stats_collaborator.bad_fruits_eaten += 1

            if self.stationary:
                self.bad_fruit_revealed = True

         # About to cross lava
        elif next_move_collaborator in self.lava:
            self.collaborator.move()

            if very_bad_sound and PLAY_SOUND:
                good_sound.play()
            #    very_bad_sound.play()

            #self.generate_lava(1) 
            self.lava.remove(next_move_collaborator)          
            reward_collaborator += self.rewards['good_fruit']
            self.stats_collaborator.lava_crossed += 1

            if self.stationary:
                self.lava_revealed = True

        elif next_move_collaborator in self.pit:
            if not self.in_pit:
                self.collaborator.move()
                self.original_direction = self.collaborator.direction
                #if stuck_sound and PLAY_SOUND:
                #    stuck_sound.play()
            else:
                stuck = True
            reward_collaborator += self.rewards['timestep']
            self.in_pit = True

        # If not, just move forward.
        else:
            self.collaborator.move()
            reward_collaborator += self.rewards['timestep']
            
        '''
        if self.collaboration: 
            self.field.update_snake_footprint(old_head, old_tail, self.snake.head, self.collaborator.head, self.collaborator.tail)
        else:
            self.field.update_snake_footprint(old_head, old_tail, self.snake.head)
        '''

        if self.collaboration: 
            self.field.update_snake_footprint(old_head, old_tail, self.snake.head, self.collaborator)
        else:
            self.field.update_snake_footprint(old_head, old_tail, self.snake.head)
           
        self.field.update_collaborator_footprint(old_head_collaborator, old_tail_collaborator, self.collaborator.head, self.snake)
        if stuck:
            if stuck_sound and PLAY_SOUND:
                stuck_sound.play()

        # Hit a wall or own body?
        if not self.is_alive():
            if self.has_hit_wall():
                self.stats.termination_reason = 'hit_wall'   
            if self.has_hit_own_body():
                self.stats.termination_reason = 'hit_own_body'
            self.field[self.snake.head] = CellType.SNAKE_HEAD
            self.is_game_over = True
            reward = self.rewards['died']
            
        # Hit a wall or own body? (Collaborator)
        if not self.is_alive(self.collaborator):
            if self.has_hit_wall(self.collaborator):
                self.stats_collaborator.termination_reason = 'hit_wall'   
            if self.has_hit_own_body(self.collaborator):
                self.stats_collaborator.termination_reason = 'hit_own_body'
            self.field[self.collaborator.head] = CellType.SNAKE_HEAD
            self.is_game_over = True
            reward_collaborator = self.rewards['died']

        # Stationary environment? (terminates when reaches an item)
        if self.stationary:
            if reward != 0:
                self.is_game_over = True
                self.stats.termination_reason = 'successfully reached an item'

        # Exceeded the limit of moves?
        if self.timestep_index >= self.max_step_limit:
            self.is_game_over = True
            self.stats.termination_reason = 'timestep_limit_exceeded'
            self.stats_collaborator.termination_reason = 'timestep_limit_exceeded'

        result = TimestepResult(
            observation=self.get_observation(),
            reward=reward,
            is_episode_end=self.is_game_over
        )
        
        result_collaborator = TimestepResult(
            observation=self.get_observation(),
            reward=reward_collaborator,
            is_episode_end=self.is_game_over
        )
        
        self.record_timestep_stats(result, agent_mode)
        self.record_timestep_stats_collaborator(result_collaborator, agent_mode)
        
        return result, result_collaborator
    
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
    
    def has_hit_wall(self, agent=None):
        """ True if the snake has hit a wall, False otherwise. """
        if agent is None: agent = self.snake
        return self.field[agent.head] == CellType.WALL

    def has_hit_own_body(self, agent=None):
        """ True if the snake has hit its own body, False otherwise. """
        if agent is None: agent = self.snake
        return self.field[agent.head] == CellType.COLLABORATOR_BODY

    def is_alive(self, agent=None):
        """ True if the snake is still alive, False otherwise. """
        if agent is None: agent = self.snake
        return not self.has_hit_wall(agent=agent) and not self.has_hit_own_body(agent=agent)


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
            self.action_counter[action] += 1

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
