import random
import numpy as np
from robotaxi.agent import AgentBase
from robotaxi.gameplay.entities import ALL_SNAKE_ACTIONS, CellType
from robotaxi.agent import ValueIterationAgent
from robotaxi.detectors.feedback_detector import *
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.cbook import get_sample_data
from matplotlib import gridspec
import threading
import time
import robotaxi

matplotlib.rcParams['toolbar'] = 'None'
robotaxi_path = os.path.dirname(robotaxi.gameplay.environment.__file__)


class RewardLearningAgent(AgentBase):
    """ Represents a agent that takes an action by 
        choosing actions between value-iteration agents
        under different rewards. """

    def __init__(self, participant_id='webcam', belief=[1.0,1.0,1.0,1.0,1.0,1.0]):
    
        #random.seed(12345)
        random.seed(int(time.time()))
        
        self.reward_matchings = [(0,1,2), (1,0,2), (0,2,1), (1,2,0), (2,0,1), (2,1,0)]
        self.reward_mappings = [
            { # go for good fruit
                CellType.SNAKE_HEAD: 0,
                CellType.SNAKE_BODY: 0,
                CellType.GOOD_FRUIT: 60,
                CellType.BAD_FRUIT:  -10,
                CellType.LAVA: -50,
                CellType.EMPTY: -1,
                CellType.WALL: -10,
            },{ # go for good fruit and bad fruit
                CellType.SNAKE_HEAD: 0,
                CellType.SNAKE_BODY: 0,
                CellType.GOOD_FRUIT: 60,
                CellType.BAD_FRUIT: -50,
                CellType.LAVA: -10,
                CellType.EMPTY: -1,
                CellType.WALL: -10,
            }, { # go for bad fruit
                CellType.SNAKE_HEAD: 0,
                CellType.SNAKE_BODY: 0,
                CellType.GOOD_FRUIT: -10,
                CellType.BAD_FRUIT: 60,
                CellType.LAVA: -50,
                CellType.EMPTY: -1,
                CellType.WALL: -10,
            }, { # go for bad fruit 
                CellType.SNAKE_HEAD: 0,
                CellType.SNAKE_BODY: 0,
                CellType.GOOD_FRUIT: -50,
                CellType.BAD_FRUIT: 60,
                CellType.LAVA: -10,
                CellType.EMPTY: -1,
                CellType.WALL: -10,
            }, { # go for lava
                CellType.SNAKE_HEAD: 0,
                CellType.SNAKE_BODY: 0,
                CellType.GOOD_FRUIT: -10,
                CellType.BAD_FRUIT: -50,
                CellType.LAVA: 60,
                CellType.EMPTY: -1,
                CellType.WALL: -10,
            }, { # go for lava 
                CellType.SNAKE_HEAD: 0,
                CellType.SNAKE_BODY: 0,
                CellType.GOOD_FRUIT: -50,
                CellType.BAD_FRUIT: -10,
                CellType.LAVA: 60,
                CellType.EMPTY: -1,
                CellType.WALL: -10,
            }]
        self.beliefs = []
        self.agents = []
        for reward_mapping_idx in range(len(self.reward_mappings)):
            print(reward_mapping_idx, self.reward_matchings[reward_mapping_idx] )
            print(self.reward_mappings[reward_mapping_idx])
            self.agents.append(ValueIterationAgent(reward_mapping=self.reward_mappings[reward_mapping_idx]))
        self.belief = np.array(belief)/np.sum(belief)
        self.p = [1/3.0,1/3.0,1/3.0]
        self.set_probabilities()        
        self.curr_agent = 5 #random.randint(2,5)
        self.last_action = None
        self.feedback_detector = FeedbackDetector(participant_id)
        self.started = False
        self.beta = 0.05
        self.num_updates = 1
        self.x_pos = [r for r in range(len(self.reward_matchings))]
        self.x = [str(comb) for comb in self.reward_matchings]
        self.action_ct = 0
        now = time.time()
        self.log_file = open('./log/online_learning_log_'+str(int(now*10))+'.csv', 'w')
        reward_str = ','.join([str(m) for m in self.reward_matchings])
        self.log_file.write('action_ct, update_ct, optimal, entropy, ' + reward_str + '\n')
        self.last_num_updates = 0
        self.icons = [plt.imread(get_sample_data(robotaxi_path+'/../../icon/' + icon_name)) for icon_name in ['purple_car.png','road_block.png','man.png']]
        
        #self.fig = plt.figure(figsize=(10, 3.5)) 
        #gs = gridspec.GridSpec(1, 2, width_ratios=[1, 2]) 
        
        self.fig, (self.ax_update, self.ax0, self.ax1) = plt.subplots(1, 3, figsize=(13.2, 2.5), gridspec_kw={'width_ratios': [1, 2, 4]})
        self.fig.canvas.set_window_title('Belief Updates') 
        
        self.ax_update.set_title("Last Pickup")
        self.ax_update.axis('off')
        #self.ax_update.imshow(self.icons[0], aspect='auto', extent=(0.5,0.8,0.5,0.8), zorder=-1)
        
        #self.ax0.set_xlabel("Reward Type")
        self.ax0.set_ylabel("Probability", fontsize=12)
        self.ax0.set_title("Predicted reward category of last pickup", fontsize=12)
        self.ax0.bar(self.x_pos[:3], [0.33,0.33,0.33], color=["red","yellow","green"])  
        #self.ax0.set_xticks([])              
        self.ax0.set_xticks(self.x_pos[:3])
        self.ax0.tick_params(axis='x', which='major', pad=15)
        self.ax0.set_xticklabels([" "," "," "])
        self.ax0.set_ylim(0,1.0)       
        
        newax = self.fig.add_axes([0.07+0.03, 0.03, 0.15, 0.15], anchor='NE', zorder=0)
        newax.imshow(self.icons[0])
        newax.axis('off')
        newax = self.fig.add_axes([0.07+0.11, 0.03, 0.15, 0.15], anchor='NE', zorder=0)
        newax.imshow(self.icons[1])
        newax.axis('off')
        newax = self.fig.add_axes([0.07+0.19, 0.03, 0.15, 0.15], anchor='NE', zorder=0)
        newax.imshow(self.icons[2])
        newax.axis('off')
        
        #self.ax1.set_xlabel("Reward Mapping")
        self.ax1.set_ylabel("Probability", fontsize=12)
        self.ax1.set_title("Belief over Reward Mappings", fontsize=12)
        self.ax1.bar(self.x_pos, self.belief, color=[(1-m.index(2)/2.0, m.index(2)/2.0, 0.4) for m in self.reward_matchings])                
        self.ax1.set_xticks(self.x_pos)
        self.ax1.set_xticklabels([" "," "," "," "," "," "])
        self.ax1.set_ylim(0,1.0)
        self.ax1.tick_params(axis='x', which='major', pad=15)
        
        pos_ct = 0
        mapping_ct = 0
        for comb in self.reward_matchings:
            mapping_ct += 1
            for item in comb:
                newax = self.fig.add_axes([0.44+pos_ct*0.022+mapping_ct*0.012, 0.035, 0.075, 0.075], anchor='NE', zorder=0)
                newax.imshow(self.icons[item])
                newax.axis('off')
                pos_ct += 1
        #self.ax1.set_xticklabels(self.x)
        
            
        colors = {'go for passenger':(1-2/2.0, 2/2.0, 0.4), 'go for road-block':(1-1/2.0, 1/2.0, 0.4), 'go for parked car':(1-0/2.0, 0/2.0, 0.4)}         
        self.labels = list(colors.keys())
        self.handles = [plt.Rectangle((0,0),1,1, color=colors[label]) for label in self.labels]
        self.ax1.legend(self.handles, self.labels, ncol=3)

        self.pickup_list = []
        
        plt.tight_layout()
        plt.pause(0.0001)
        
    
    def logsumexp(self, nums):
        max_num = max(nums)
        total = sum([np.exp(num-max_num) for num in nums])
        return np.log(total) + max_num
        
    def set_probabilities(self):
        self.probabilities = [ p/sum(self.belief) for p in self.belief]
        for i in range(1,len(self.probabilities)): self.probabilities[i] += self.probabilities[i-1]
            
    def begin_episode(self):
        self.step_ct = 0
        
    def kl_divergence(self, p, q):
        return np.sum(np.where(p != 0, p * np.log(p / q), 0))
    
    def update_belief(self):
        
        reward_matching_idx = 3 - self.agents[self.curr_agent].last_pickup
        print('last pickup:', reward_matching_idx)
        self.pickup_list.append(reward_matching_idx)
        prior = np.array(list(self.belief)) # prior
        time.sleep(1.6)        
        p = self.feedback_detector.peek()
        self.p = p
        #print('updating thread starts with arg', p)
        self.num_updates += 1
        posterior = [0.0]*len(self.belief)
        for i in range(len(self.agents)):
            posterior[i] += p[self.reward_matchings[i][reward_matching_idx]]  
        for i in range(len(self.agents)):
            posterior[i] = np.exp(posterior[i])
        posterior = np.array(posterior)
        posterior /= np.sum(posterior)
        self.beliefs.append(posterior)
        #kl_w = min(1.0,self.kl_divergence(prior, posterior))
        #self.belief = kl_w * prior + (1.0-kl_w) * posterior 
        
        self.belief = np.prod(self.beliefs, axis = 0)
        self.belief /= np.sum(self.belief)                
        self.set_probabilities()
        entropy = - sum([b*np.log(b) for b in self.belief])

        optimal = False
        if self.belief[0] == max(self.belief) and self.belief[0] > 1.0/6 or self.belief[3] == max(self.belief) and self.belief[3] >  1.0 / 6: optimal = True
        self.log_file.write(str(self.action_ct)+',' + str(self.num_updates)+','+str(optimal)+','+ str(entropy) + ','+ ','.join([str(b) for b in self.belief]) + '\n')
        #print("updated belief: ")
        #for b in self.belief: print(b, end='\t')
        #print()            
        
    
    def act(self, observation, reward):
        if not self.started:
            self.feedback_detector.start()
            self.started = True

        for i in range(len(self.agents)):
            agent = self.agents[i]
            agent.compute_reward_map(observation)
            
        if not self.agents[self.curr_agent].last_pickup is None:            
            if not self.last_action is None:
                time.sleep(0.5)
                thread = threading.Thread(target=self.update_belief)
                thread.start()                
        
        
        
        if self.num_updates - self.last_num_updates > 0:
            
            if len(self.pickup_list) > 0:
                self.ax_update.clear()
                self.ax_update.set_title("Last Pickup")
                self.ax_update.axis('off')
                self.ax_update.imshow(self.icons[self.pickup_list.pop(0)], aspect='auto', extent=(0.5,0.8,0.5,0.8), zorder=-1)
            
            self.ax0.clear()
            self.ax1.clear()
            
            self.ax0.set_ylabel("Probability", fontsize=12)
            self.ax0.set_title("Predicted reward category of last pickup", fontsize=12)
            self.ax0.bar(self.x_pos[:3], self.p, color=["red","yellow","green"])    
            self.ax0.set_xticks(self.x_pos[:3])
            self.ax0.tick_params(axis='x', which='major', pad=15)
            self.ax0.set_xticklabels([" "," "," "])                      
            self.ax0.set_ylim(0,1.0)       
           
            self.ax1.set_ylabel("Probability", fontsize=12)
            self.ax1.set_title("Belief over Reward Mappings", fontsize=12)
            self.ax1.bar(self.x_pos, self.belief, color=[(1-m.index(2)/2.0, m.index(2)/2.0, 0.4) for m in self.reward_matchings])                
            self.ax1.set_xticks(self.x_pos)
            self.ax1.tick_params(axis='x', which='major', pad=15)
            self.ax1.set_xticklabels([" "," "," "," "," "," "])
            self.ax1.set_ylim(0,1.0)        
            self.ax1.legend(self.handles, self.labels, ncol=3)
        
            plt.pause(0.0001)        
            
            self.last_num_updates = self.num_updates
            
        if self.agents[self.curr_agent].env_changed:            
            if self.num_updates == 0 or random.random() < 0.8: 
                p = random.random()
                for i in range(len(self.reward_mappings)):
                    if p < self.probabilities[i]:
                        self.curr_agent = i
                        break
            else:
                agent_idxes = np.argwhere(np.array(self.belief) == self.belief[np.argmax(self.belief)] )
                self.curr_agent = random.choice(agent_idxes)[0]    
                
        action = self.agents[self.curr_agent].act(observation, reward)
        self.last_action = (observation, action)
        self.action_ct += 1
        return action
                
    def end_episode(self):
        self.feedback_detector.stop()
        self.log_file.close()
        
