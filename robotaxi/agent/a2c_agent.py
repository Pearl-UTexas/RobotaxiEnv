import sys
import random
import copy
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

import torch
from torch.autograd import Variable
from robotaxi.agent import AgentBase
from policy_learning.a2c_ppo_acktr.gameplay.entities import CellType, Point, SnakeAction, SnakeDirection, ALL_SNAKE_ACTIONS, ALL_SNAKE_DIRECTIONS

from keras.utils import to_categorical

import  policy_learning.a2c_ppo_acktr
from policy_learning.a2c_ppo_acktr.model import Policy


class OpenAIGymActionSpaceAdapter(object):
    """ Converts the Snake action space to OpenAI Gym action space format. """

    def __init__(self, actions):
        self.actions = np.array(actions)
        self.shape = self.actions.shape
        self.n = len(self.actions)
        self.__class__.__name__= "Discrete"

    def sample(self):
        return np.random.choice(self.actions)



class A2CAgent(AgentBase):
    """ Represents a Snake agent that runs value iteration at every step (when nothing was eaten). """

    def __init__(self, grid_size=8, discount=0.95, reward_mapping=None, env=None, mixed=True):
        # 18 * 18 (gridsize-2) * 4 (four directions)
        self.grid_size = grid_size
        self.env = env
        self.num_states = ((grid_size-2)**2)*len(ALL_SNAKE_DIRECTIONS)
        self.num_actions = len(ALL_SNAKE_ACTIONS)
        if mixed:
            self.actor_critic = Policy(
                        (7*8*8+1,) ,
                        OpenAIGymActionSpaceAdapter(ALL_SNAKE_ACTIONS),
                        base_kwargs={'recurrent': False})
            weights, self.ob_rms = torch.load('./policy_learning/trained_models/a2c/snake_weights_mixed.pt')
        else:
            self.actor_critic = Policy(
                        (7*8*8,) ,
                        OpenAIGymActionSpaceAdapter(ALL_SNAKE_ACTIONS),
                        base_kwargs={'recurrent': False})
            weights, self.ob_rms = torch.load('./policy_learning/trained_models/a2c/snake_weights_vi.pt')
        self.epsilon = 1e-5
        self.clipob = 10.0
        self.gamma = 0.99
        self.actor_critic.load_state_dict(weights)
        self.actor_critic.double()
        self.actor_critic.cuda()
        self.actor_critic.eval()
        self.recurrent_hidden_states = torch.zeros(1, self.actor_critic.recurrent_hidden_state_size)
        self.masks = torch.zeros(1, 1)

        self.action_dict = { 
                             SnakeDirection.WEST: np.array([[0,-1],[1,0],[-1,0]]),
                             SnakeDirection.EAST: np.array([[0,1],[-1,0],[1,0]]),
                             SnakeDirection.NORTH: np.array([[-1,0],[0,-1],[0,1]]),
                             SnakeDirection.SOUTH: np.array([[1,0],[0,1],[0,-1]])
                           }
        
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
        
        self.reward_map = {
            CellType.EMPTY:0,
            CellType.GOOD_FRUIT:6.0,
            CellType.BAD_FRUIT:-1.0,
            CellType.LAVA:-5.0,
            CellType.SNAKE_HEAD:0,
            CellType.SNAKE_BODY:0,
            CellType.WALL:0,
            CellType.DUMMY:0,
        }


    def begin_episode(self):
        pass
    
    def get_cell(self, point):
        """ Get the type of cell at the given point. """
        x, y = point
        return self.cells[y, x]

    def get_q_value(self, obs, action):
        next_obs = []
        #print('obs:',obs)
        #print('action:',action)
        head = [0,0]
        body = [0,0]
        for x in range(len(obs)):
            next_obs.append([])
            for y in range(len(obs[x])):
                if self.data_to_cell_type[obs[x][y]] == CellType.SNAKE_HEAD:
                    next_obs[-1].append(CellType.EMPTY)
                    head =np.array([x, y])
                    if self.data_to_cell_type[obs[x-1][y]] == CellType.SNAKE_BODY:
                        state_direction = SnakeDirection.SOUTH
                    elif self.data_to_cell_type[obs[x+1][y]] == CellType.SNAKE_BODY:
                        state_direction = SnakeDirection.NORTH
                    elif self.data_to_cell_type[obs[x][y-1]] == CellType.SNAKE_BODY:
                        state_direction = SnakeDirection.EAST
                    elif self.data_to_cell_type[obs[x][y+1]] == CellType.SNAKE_BODY:
                        state_direction = SnakeDirection.WEST
                    else:
                        print("No snake body detected!!!!!") # shouldn't be here
                elif self.data_to_cell_type[obs[x][y]] == CellType.SNAKE_BODY:
                    next_obs[-1].append(CellType.EMPTY)
                else:
                    next_obs[-1].append(obs[x][y])
        next_obs[head[0]][head[1]] = CellType.SNAKE_BODY
        next_head = head + self.action_dict[state_direction][action]
        if next_obs[next_head[0]][next_head[1]] == CellType.WALL:
            if next_head[0] == 0:
                next_head[0] += 1
                if next_head[1] < 4: next_head[1] += 1
                else: next_head[1] -= 1
            elif next_head[0] == 8:
                next_head[0] -= 1
                if next_head[1] < 4: next_head[1] += 1
                else: next_head[1] -= 1
            elif next_head[1] == 0:
                next_head[1] += 1
                if next_head[0] < 4: next_head[0] += 1
                else: next_head[0] -= 1
            elif next_head[1] == 8:
                next_head[1] -= 1
                if next_head[0] < 4: next_head[0] += 1
                else: next_head[0] -= 1
        next_obs[next_head[0]][next_head[1]] = CellType.SNAKE_HEAD
        #print('next_obs:')
        #for row in next_obs: print(row)
        qval = self.reward_map[obs[next_head[0]][next_head[1]]]
        value = self.get_val(next_obs)
        '''
        obs = next_obs
        obs = to_categorical(obs)
        obs = np.moveaxis(obs, -1, 0)
        obs = obs.flatten()
        obs = np.array(np.clip((obs - self.ob_rms.mean) /
                          np.sqrt(self.ob_rms.var + self.epsilon),
                          -self.clipob, self.clipob)).astype('double')
        obs = torch.from_numpy(obs).double()
        action = np.expand_dims(action, axis=0)
        action = torch.from_numpy(np.array(action)).double()
        value, action_log_probs, _, _ = self.actor_critic.evaluate_actions(obs.cuda(), self.recurrent_hidden_states, self.masks, action.cuda())
        '''
        qval += value*self.gamma
        return qval

    def get_val(self, observation, agent=None):
        obs = to_categorical(observation)
        obs = np.moveaxis(obs, -1, 0)
        obs = obs.flatten()
        if agent is not None:
            obs = np.append(obs, agent)
        obs = np.array(np.clip((obs - self.ob_rms.mean) /
                      np.sqrt(self.ob_rms.var + self.epsilon),
                      -self.clipob, self.clipob)).astype('double')
        obs = torch.from_numpy(obs).double()
        value = self.actor_critic.get_value(obs.cuda(), self.recurrent_hidden_states, self.masks)
        return value.item()

    def act(self, observation, reward=0.0):
        
        max_q_a = 0
        max_q = 0
        qvals = []
        for a in range(3): 
            qval = self.get_q_value(observation, a)
            qvals.append(qval)
            if qval > max_q:
                max_q = qval
                max_q_a = a
        qvals = np.array(qvals)
        qvals = np.divide(np.exp(qvals),np.sum(np.exp(qvals)))
        p = np.random.random()
        for a in range(3): 
          if p > np.sum(qvals[0:a+1]):
            max_q_a = a
            break
        '''
        obs = to_categorical(observation)
        obs = np.moveaxis(obs, -1, 0)
        obs = obs.flatten()
        obs = np.array(np.clip((obs - self.ob_rms.mean) /
                          np.sqrt(self.ob_rms.var + self.epsilon),
                          -self.clipob, self.clipob)).astype('double')
        obs = torch.from_numpy(obs).double()
        value, selected_action, _, self.recurrent_hidden_states = self.actor_critic.act(obs.cuda(), self.recurrent_hidden_states, self.masks, deterministic=False)
        print(max_q_a, selected_action.item())
        '''
        return  max_q_a #selected_action.item()

    def end_episode(self):
        pass

  

   
