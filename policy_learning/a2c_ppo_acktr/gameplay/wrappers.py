""" Provides adapters for other AI/RL frameworks, such as OpenAI Gym. """

import json
import numpy as np

from .entities import ALL_SNAKE_ACTIONS, CellType
from .environment import Environment

from gym import spaces

from keras.utils import to_categorical


class Colors:

    CELL_TYPE = {
        CellType.WALL: (26, 26, 26),
        CellType.SNAKE_BODY: (82, 154, 255),
        CellType.SNAKE_HEAD: (65, 132, 255),
        CellType.GOOD_FRUIT: (85, 242, 240),
        CellType.BAD_FRUIT: (177, 242, 85),
        CellType.LAVA: (150, 53, 219),
        CellType.EMPTY: (129, 129, 129),
    }
    
    
class OpenAIGymEnvAdapter(object):
    """ Converts the Snake environment to OpenAI Gym environment format. """

    def __init__(self, env, action_space, observation_shape, agent):
        self.env = env
        self.action_space = OpenAIGymActionSpaceAdapter(action_space)
        self.field_size = 8
        self.obs_shape = (7*observation_shape[0]*observation_shape[1]+1,)        
        self.observation_space = spaces.Box(low=0, high=6, shape=self.obs_shape, dtype=np.float32)
        self.reward_range = (-float('inf'), float('inf'))
        self.metadata = {'render.modes': []}
        self.spec = None
        self.curr_frame = None
        self.initial_frame = None
        self.agent = agent
        self.frame_data_to_cell_type = {         
            0: CellType.EMPTY,
            1: CellType.GOOD_FRUIT,
            2: CellType.BAD_FRUIT,
            3: CellType.LAVA,
            4: CellType.SNAKE_HEAD,
            5: CellType.SNAKE_BODY,
            6: CellType.WALL,
            7: CellType.DUMMY,
        }
        
        
    def seed(self, value):
        self.env.seed(value)

    def convert_to_img(self, observation):
        frame = np.zeros(self.obs_shape)
        for x in range(self.field_size):
            for y in range(self.field_size):
                cell_type = self.frame_data_to_cell_type[observation[y][x]]
                cell_color = Colors.CELL_TYPE[cell_type]
                frame[0][x][y] = cell_color[0]
                frame[1][x][y] = cell_color[1]
                frame[2][x][y] = cell_color[2]
        return frame

    def reset(self):        
        tsr = self.env.new_episode()
        self.initial_frame = list(tsr.observation)
        self.curr_frame = tsr.observation  
              
        frame = to_categorical(tsr.observation)
        frame = np.moveaxis(frame, -1, 0)
        data = frame.flatten()
        data = np.append(data, self.agent.curr_agent)
        return data, self.curr_frame

    def step(self, action):
    
        self.env.choose_action(action)
        timestep_result = self.env.timestep()
        tsr = timestep_result
        self.curr_frame = tsr.observation
        
        frame = to_categorical(tsr.observation)
        frame = np.moveaxis(frame, -1, 0)
        reward = tsr.reward
        #if reward > 0: reward *= 10
        data = frame.flatten()
        data = np.append(data, self.agent.curr_agent)
        return data, reward, tsr.is_episode_end, {'raw_data':self.curr_frame, 'initial_data':self.initial_frame} 
    
    def render(self, mode=None):
        pass
        #print(self.curr_frame)


class OpenAIGymActionSpaceAdapter(object):
    """ Converts the Snake action space to OpenAI Gym action space format. """

    def __init__(self, actions):
        self.actions = np.array(actions)
        self.shape = self.actions.shape
        self.n = len(self.actions)
        self.__class__.__name__= "Discrete"

    def sample(self):
        return np.random.choice(self.actions)


def make_openai_gym_environment(config_filename, agent):
    """
    Create an OpenAI Gym environment for the Snake game.
    
    Args:
        config_filename: JSON config for the Snake game level.

    Returns:
        An instance of OpenAI Gym environment.
    """

    with open(config_filename) as cfg:
        env_config = json.load(cfg)

    env_raw = Environment(config=env_config, verbose=0)
    env = OpenAIGymEnvAdapter(env_raw, ALL_SNAKE_ACTIONS, (8, 8), agent)
    return env
