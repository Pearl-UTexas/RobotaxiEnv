import random

from robotaxi.agent import AgentBase
from robotaxi.gameplay.entities import ALL_SNAKE_ACTIONS, CellType
from robotaxi.agent import ValueIterationAgent

class MixedActionAgent(AgentBase):
    """ Represents a Snake agent that takes an action by 
        randomly choosing actions between value-iteration agents
        under different rewards. """

    def __init__(self, schedule=[[1.0,1.0,4.0]], total_steps=200, grid_size=8, env=None, level_file=None):
        self.reward_mappings = [
            { # go for good fruit
                CellType.SNAKE_HEAD: 0,
                CellType.SNAKE_BODY: 0,
                CellType.GOOD_FRUIT: 6,
                CellType.BAD_FRUIT:  -1,
                CellType.LAVA: -5,
                CellType.EMPTY: 0,
                CellType.PIT: 0,
                CellType.WALL: -100,
            }, { # go for bad fruit
                CellType.SNAKE_HEAD: 0,
                CellType.SNAKE_BODY: 0,
                CellType.GOOD_FRUIT: -1,
                CellType.BAD_FRUIT: 6,
                CellType.LAVA: -5,
                CellType.EMPTY: 0,
                CellType.PIT: 0,
                CellType.WALL: -100,
            }, { # go for lava
                CellType.SNAKE_HEAD: 0,
                CellType.SNAKE_BODY: 0,
                CellType.GOOD_FRUIT: -1,
                CellType.BAD_FRUIT: -5,
                CellType.LAVA: 6,
                CellType.EMPTY: 0,
                CellType.PIT: 0,
                CellType.WALL: -100,
            }]
        self.probabilities = []
        for probabilities in schedule:
            self.probabilities.append([ p/sum(probabilities) for p in probabilities])
            for i in range(1,len(self.probabilities[-1])): self.probabilities[-1][i] += self.probabilities[-1][i-1]
        self.agents = []
        for reward_mapping_idx in range(len(self.reward_mappings)):
            self.agents.append(ValueIterationAgent(reward_mapping=self.reward_mappings[reward_mapping_idx], grid_size=grid_size, env=env, level_file=level_file))
        self.step_ct = 0
        self.total_steps = total_steps
        self.step_idx_factor = self.total_steps//len(self.probabilities)
        random.seed(158462555)
        self.curr_agent = random.randint(0,len(self.reward_mappings)-1)

    def update_env(self, env):
        for agent in self.agents:
            agent.update_env(env)
    
    def begin_episode(self):
        self.step_ct = 0
        self.curr_agent = random.randint(0,len(self.reward_mappings)-1)

    def act(self, observation, reward=0.0):
        
        p = random.random()
        p_index = min(self.step_ct//self.step_idx_factor,len(self.probabilities)-1)
        #print(p_index, self.step_ct )
        if self.agents[self.curr_agent].env_changed or random.random() < 0.1:
            for i in range(len(self.reward_mappings)):
                if p < self.probabilities[p_index][i]:
                    next_agent = i
                    break
            self.curr_agent = next_agent
            self.step_ct += 1
        
        return self.agents[self.curr_agent].act(observation, reward)

                
    def end_episode(self):
        pass
