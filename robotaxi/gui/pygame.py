import numpy as np
import pygame
import time
import random
import cv2
import os

import threading
import robotaxi
from robotaxi.agent import HumanAgent
from robotaxi.gameplay.entities import (CellType, SnakeAction, SnakeDirection, ALL_SNAKE_DIRECTIONS, ALL_SNAKE_ACTIONS, SNAKE_GROW, WALL_WARP, Point)
from robotaxi.gameplay.environment import PLAY_SOUND

robotaxi_path = os.path.dirname(robotaxi.gameplay.environment.__file__)
#print(robotaxi_path)


frame_ct = -1

class captureThread(threading.Thread):

    def __init__(self, threadID,  participant='test', data_dir='./user_study_data/', exp_id='collaborative', test=False):  
        super(captureThread, self).__init__()
        #threading.Thread.__init__(self)
        self._stop_event = threading.Event()
        self.threadID = threadID
        self.prefix = participant+'_'+exp_id
        self.data_dir = data_dir
        self.participant = participant
        self.exp_id = exp_id

        if not test: self.store_dir = data_dir+'webcam_imgs/'+participant+'/'+exp_id
        else: self.store_dir = data_dir+'webcam_imgs/'+participant+'/'+exp_id + '_test'
        if not os.path.exists(data_dir+'webcam_imgs/'+participant):
            os.makedirs(data_dir+'webcam_imgs/'+participant)        
        if not os.path.exists(self.store_dir):
            os.makedirs(self.store_dir)
        
    def run(self):        
        global frame_ct        
        print ("Starting " + self.name + ' at ' + time.ctime(time.time()))       
        cap = cv2.VideoCapture(0)
        while frame_ct == -1: 
            time.sleep(0.01)
        img_ct = 0
        while(cap.isOpened()):
            ret, frame = cap.read()
            if ret==True:                   
                cv2.imwrite(self.store_dir+'/'+self.prefix+'_'+str(round(time.time()*1000))+'_'+str(frame_ct)+'_'+str(img_ct)+'.jpg', frame)
                img_ct += 1
                if self._stop_event.is_set(): break                

        cap.release()
        cv2.destroyAllWindows()
        print ("Exiting cam")
    
    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
        
        
class PyGameGUI:
    """ Provides a Snake GUI powered by Pygame. """

    FPS_LIMIT = 60
    AI_TIMESTEP_DELAY = 500
    HUMAN_TIMESTEP_DELAY = 500

    SNAKE_CONTROL_KEYS = [
        pygame.K_UP,
        pygame.K_LEFT,
        pygame.K_DOWN,
        pygame.K_RIGHT
    ]

    def __init__(self, save_frames=False, field_size=8, test=False):
        #pygame.mixer.pre_init(44100, -16, 2, 32)
        pygame.init()
        pygame.mixer.init()
        
        pygame.mouse.set_visible(False)
        self.base_dir = robotaxi_path + '/../../'
        self.punch_sound = pygame.mixer.Sound(self.base_dir+'sound/punch.wav')
        self.begin_sound = pygame.mixer.Sound(self.base_dir+'sound/begin.wav')
        self.good_sound = pygame.mixer.Sound(self.base_dir+'sound/good.wav')
        self.bad_sound = pygame.mixer.Sound(self.base_dir+'sound/road_block_crash.wav')
        self.very_bad_sound = pygame.mixer.Sound(self.base_dir+'sound/car_crash.wav')
        self.stuck_sound = pygame.mixer.Sound(self.base_dir+'sound/woop.wav')
        self.free_sound = pygame.mixer.Sound(self.base_dir+'sound/restart.wav')
        self.agent = HumanAgent()
        self.collaborating_agent = None
        self.env = None
        self.screen = None
        self.screen_size = 0
        self.fps_clock = None
        self.timestep_watch = Stopwatch()
        self.time_thresh = 50 # threshold for timestep left to render red and flash
        self.frame_num = 0
        self.pause = True
        self.sound_played = True
        self.display_time = False
        self.save_frames = save_frames
        self.timestep_delay = 0
        self.intermediate_frames = 21
        self.FIELD_SIZE = field_size
        self.CELL_SIZE = 96*8//self.FIELD_SIZE

        self.car_schemes = ["auto_bus","pickup","truck"]
        self.selected_icon_scheme = 0 # default
        self.set_icon_scheme(self.selected_icon_scheme)
        self.selected_icon_scheme_collaborator = 0
        self.set_icon_scheme_collaborator(self.selected_icon_scheme_collaborator)
        self.selected = False
        
        self.test = test

        self.spawn_icon = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/wave.png"),(self.CELL_SIZE, self.CELL_SIZE))
        self.wall_icon = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/forest.png"),(self.CELL_SIZE, self.CELL_SIZE))
        self.good_fruit_icon = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/man.png"),(self.CELL_SIZE*2//3, self.CELL_SIZE*2//3))
        self.bad_fruit_icon = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/road_block.png"),(self.CELL_SIZE*2//3, self.CELL_SIZE*2//3))
        self.lava_icon = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/purple_car.png"),(self.CELL_SIZE, self.CELL_SIZE))
        self.small_crash_icon = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/road_block_broken.png"),(self.CELL_SIZE*2//3, self.CELL_SIZE*2//3))
        self.big_crash_icon = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/broken_purple_car.png"),(self.CELL_SIZE, self.CELL_SIZE*2//3))
        self.reward_icon = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/dollar.png"),(self.CELL_SIZE//3, self.CELL_SIZE//3))
        self.curr_icon = None
        self.curr_icon_collaborator = None
        self.question1_icon = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/question1.png"),(self.CELL_SIZE*2//3, self.CELL_SIZE*2//3))
        self.question2_icon = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/question2.png"),(self.CELL_SIZE*2//3, self.CELL_SIZE*2//3))
        self.question3_icon = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/question3.png"),(self.CELL_SIZE*2//3, self.CELL_SIZE*2//3))
        self.pit_icon = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/stopped.png"),(self.CELL_SIZE, self.CELL_SIZE))
        self.stop_icon = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/stopped.png"),(self.CELL_SIZE//3, self.CELL_SIZE//3))
        self.accident_icon = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/mad.png"),(self.CELL_SIZE*2//3, self.CELL_SIZE*2//3))
        #self.head_icon = pygame.transform.scale(pygame.image.load("icon/snake.png"),(self.CELL_SIZE, self.CELL_SIZE))
        #self.body_icon = pygame.transform.scale(pygame.image.load("icon/body.png"),(self.CELL_SIZE, self.CELL_SIZE))
        self.punch_icon = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/scary_tree.png"),(self.CELL_SIZE, self.CELL_SIZE))
        self.curr_head = [0,0]
        self.last_head = [0,0]
        self.curr_head_collaborator = [0,0]
        self.last_head_collaborator = [0,0]
        self.internal_padding = self.CELL_SIZE // 5
        self.text_font = pygame.font.Font(self.base_dir+"fonts/gyparody_hv.ttf", int(23*(self.CELL_SIZE/40.0)))
        self.num_font = pygame.font.Font(self.base_dir+"fonts/gyparody_tf.ttf", int(36*(self.CELL_SIZE/40.0))) 
        self.marker_font =  pygame.font.Font(self.base_dir+"fonts/OpenSans-Bold.ttf", int(12*(self.CELL_SIZE/40.0)))
        pygame.display.set_caption('Robotaxi')

    def set_icon_scheme(self, idx):
        scheme = self.car_schemes[idx]
        self.south = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/"+scheme+"_south.png"),(self.CELL_SIZE, self.CELL_SIZE-5))
        self.north = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/"+scheme+"_north.png"),(self.CELL_SIZE, self.CELL_SIZE-5))        
        self.east = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/"+scheme+"_east.png"),(self.CELL_SIZE, self.CELL_SIZE-5))
        self.west = pygame.transform.flip(self.east,1,0)

    def set_icon_scheme_collaborator(self, idx):
        scheme = self.car_schemes[idx]
        self.south_collaborator = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/"+scheme+"_south.png"),(self.CELL_SIZE, self.CELL_SIZE-5))
        self.north_collaborator = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/"+scheme+"_north.png"),(self.CELL_SIZE, self.CELL_SIZE-5))        
        self.east_collaborator = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/"+scheme+"_east.png"),(self.CELL_SIZE, self.CELL_SIZE-5))
        self.west_collaborator = pygame.transform.flip(self.east_collaborator,1,0)

    def set_fixed_icon_scheme_collaborator(self):
        scheme = 'bulldozer'
        self.south_collaborator = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/"+scheme+"_south.png"),(self.CELL_SIZE, self.CELL_SIZE-5))
        self.north_collaborator = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/"+scheme+"_north.png"),(self.CELL_SIZE, self.CELL_SIZE-5))        
        self.east_collaborator = pygame.transform.scale(pygame.image.load(self.base_dir+"icon/"+scheme+"_east.png"),(self.CELL_SIZE, self.CELL_SIZE-5))
        self.west_collaborator = pygame.transform.flip(self.east_collaborator,1,0)

    def load_environment(self, environment):
        """ Load the RL environment into the GUI. """
        self.env = environment
        self.screen_size = ((self.env.field.size + 6) * self.CELL_SIZE, self.env.field.size * self.CELL_SIZE)
        self.screen =pygame.display.set_mode(self.screen_size) #, flags=pygame.FULLSCREEN|pygame.HWSURFACE)
        #pygame.display.set_mode(self.screen_size)
        self.screen.fill(Colors.SCREEN_BACKGROUND)
        self.total_score = 0.0

    def load_agent(self, agent, agent_name):
        """ Load the RL agent into the GUI. """
        self.agent = agent
        self.agent_name = agent_name

    def load_collaborator(self, collaborator, agent_name):
        self.collaborating_agent = collaborator
        self.collaborating_agent_name = agent_name

    def render_scoreboard(self, score, time_remaining, reward):
        # scores
        self.total_score = reward
        text = ("Earnings",'$'+str(score))
        ct = 0                
        disp_text = self.text_font.render(text[0], True, (0, 0, 0))
        disp_num = self.num_font.render(text[1], True, (0, 0, 0))
        
        # self.screen.blit(disp_text, (75+self.screen_size[0]- 4.75*self.CELL_SIZE , 15+self.screen_size[1] // 2 + self.screen_size[1] // 12 * ct - disp_text.get_height() ))
        self.screen.blit(disp_text, ((self.FIELD_SIZE+0.5)*self.CELL_SIZE, self.screen_size[1] // 2 + 0.4*self.CELL_SIZE))

        ct += 1
        cell_coords = pygame.Rect(
            (self.FIELD_SIZE+0.5)*self.CELL_SIZE,
            self.screen_size[1] // 2 + disp_num.get_height(),
            2.5*self.CELL_SIZE,
            disp_num.get_height()-10,
        )

        bar_size = 5
        if score <= 0:
            bar_coords = pygame.Rect(
                self.screen_size[0] - 1.95*self.CELL_SIZE,
                self.screen_size[1]//2,
                0.8*self.CELL_SIZE,
                -bar_size*score,
            )
        else:
            bar_coords = pygame.Rect(
                self.screen_size[0] - 1.95*self.CELL_SIZE,
                self.screen_size[1]//2-bar_size*score,
                0.8*self.CELL_SIZE,
                bar_size*score,
            )

        if reward < 0:
            delta_coords = pygame.Rect(
                self.screen_size[0] - 1.95*self.CELL_SIZE,
                self.screen_size[1]//2-bar_size*(score-reward),
                0.8*self.CELL_SIZE,
                -bar_size*reward,
            )
        elif reward > 0:
            delta_coords = pygame.Rect(
                self.screen_size[0] - 1.95*self.CELL_SIZE,
                self.screen_size[1]//2-bar_size*score,
                0.8*self.CELL_SIZE,
                bar_size*reward,
            )

        x_start = self.screen_size[0] - 2.4*self.CELL_SIZE
        x_end = self.screen_size[0] - 0.9*self.CELL_SIZE
        y = self.screen_size[1]//2

        origin_marker = self.marker_font.render("$0", True, (0, 0, 0))
        positive_marker = self.marker_font.render("+", True, (0, 0, 0))
        negative_marker = self.marker_font.render("-", True, (0, 0, 0))

        pygame.draw.line(self.screen, (0,0,0), (x_start, y), (x_end, y), 4)
        if self.collaborating_agent is not None:
            if reward > 0:
                pygame.draw.rect(self.screen, Colors.SCORE_GOOD, cell_coords)
                pygame.draw.rect(self.screen, Colors.SCORE, bar_coords)
                pygame.draw.rect(self.screen, Colors.SCORE_GOOD, delta_coords)
            elif reward < 0:
                pygame.draw.rect(self.screen, Colors.SCORE_VERY_BAD, cell_coords)
                pygame.draw.rect(self.screen, Colors.SCORE, bar_coords)
                pygame.draw.rect(self.screen, Colors.SCORE_VERY_BAD, delta_coords)
            else:
                pygame.draw.rect(self.screen, Colors.SCORE, cell_coords)
                pygame.draw.rect(self.screen, Colors.SCORE, bar_coords)
                
        else: 
            if reward == self.env.rewards['good_fruit']:
                pygame.draw.rect(self.screen, Colors.SCORE_GOOD, cell_coords)
                pygame.draw.rect(self.screen, Colors.SCORE, bar_coords)
                pygame.draw.rect(self.screen, Colors.SCORE_GOOD, delta_coords)
            elif reward == self.env.rewards['bad_fruit']:
                pygame.draw.rect(self.screen, Colors.SCORE_BAD, cell_coords)
                pygame.draw.rect(self.screen, Colors.SCORE, bar_coords)
                pygame.draw.rect(self.screen, Colors.SCORE_BAD, delta_coords)
            elif reward == self.env.rewards['lava']:
                pygame.draw.rect(self.screen, Colors.SCORE_VERY_BAD, cell_coords)
                pygame.draw.rect(self.screen, Colors.SCORE, bar_coords)
                pygame.draw.rect(self.screen, Colors.SCORE_VERY_BAD, delta_coords)
            else:
                pygame.draw.rect(self.screen, Colors.SCORE, cell_coords)
                pygame.draw.rect(self.screen, Colors.SCORE, bar_coords)

        pygame.draw.rect(self.screen, (0,0,0), bar_coords, 3)
        self.screen.blit(origin_marker, (self.screen_size[0] - 0.8*self.CELL_SIZE , self.screen_size[1] // 2 - 20 ))
        self.screen.blit(positive_marker, (self.screen_size[0] - 2.33*self.CELL_SIZE , -35+self.screen_size[1] // 2))
        self.screen.blit(negative_marker, (self.screen_size[0] - 2.3*self.CELL_SIZE , -10+self.screen_size[1] // 2))
        self.screen.blit(disp_num, ((self.FIELD_SIZE+0.9)*self.CELL_SIZE, self.screen_size[1] // 2 + self.CELL_SIZE))
        
        ct += 2
  
        if self.display_time:
            text = ("Time Left",str(round(time_remaining/(1000.0/self.timestep_delay))))
            disp_text = self.text_font.render(text[0], True, (0, 0, 0))

            if time_remaining < self.time_thresh and time_remaining%2 == 0:
                disp_num = self.num_font.render(text[1], True, (225, 50, 50))
            else:
                disp_num = self.num_font.render(text[1], True, (50, 205, 50))
            self.screen.blit(disp_text, (self.screen_size[0] - 4.75*self.CELL_SIZE , 35+self.screen_size[1] // 2 + self.screen_size[1] // 12 * ct - disp_text.get_height() ))
            ct += 1
            cell_coords = pygame.Rect(
                self.screen_size[0] - 4.5*self.CELL_SIZE ,
                70+self.screen_size[1] // 2 + self.screen_size[1] // 12 * ct - disp_num.get_height(),
                2.5*self.CELL_SIZE,
                disp_num.get_height()-10,
            )
            pygame.draw.rect(self.screen, (59,59,59), cell_coords)
            self.screen.blit(disp_num, (self.screen_size[0] - 4.1*self.CELL_SIZE , 65+self.screen_size[1] // 2 + self.screen_size[1] // 12 * ct - disp_num.get_height() ))


    def render_cell(self, x, y):
        """ Draw the cell specified by the field coordinates. """
        cell_coords = pygame.Rect(
            x * self.CELL_SIZE,
            y * self.CELL_SIZE,
            self.CELL_SIZE,
            self.CELL_SIZE,
        )
        if self.env.field[x, y] == CellType.EMPTY:
            pygame.draw.rect(self.screen, Colors.SCREEN_BACKGROUND, cell_coords)        
        elif self.env.field[x, y] == CellType.GOOD_FRUIT:
            cell_coords = pygame.Rect(
                x * self.CELL_SIZE + 5,
                y * self.CELL_SIZE + 5,
                self.CELL_SIZE,
                self.CELL_SIZE,
            )
            #if self.env.stationary and not self.env.good_fruit_revealed:
            #    self.screen.blit(self.question1_icon, cell_coords)
            #else:
            self.screen.blit(self.good_fruit_icon, cell_coords)        
        elif self.env.field[x, y] == CellType.BAD_FRUIT:
            #if self.env.stationary and not self.env.bad_fruit_revealed:
            #    self.screen.blit(self.question2_icon, cell_coords)
            #else:
            self.screen.blit(self.bad_fruit_icon, cell_coords)
        elif self.env.field[x, y] == CellType.LAVA:
            #if self.env.stationary and not self.env.lava_revealed:
            #    self.screen.blit(self.question3_icon, cell_coords)
            #else:
            self.screen.blit(self.lava_icon, cell_coords)
        elif self.env.field[x, y] == CellType.SNAKE_HEAD:
            pygame.draw.rect(self.screen, Colors.SCREEN_BACKGROUND, cell_coords)                            
            if self.env.snake.direction == SnakeDirection.NORTH:
                rotated_icon = self.north
            elif self.env.snake.direction == SnakeDirection.WEST:
                rotated_icon = self.west 
            elif self.env.snake.direction == SnakeDirection.SOUTH:
                rotated_icon = self.south
            else:
                rotated_icon = self.east
            self.curr_icon = rotated_icon               
            # self.screen.blit(rotated_icon, cell_coords)
            self.last_head = self.curr_head
            self.curr_head = [x,y]
        elif self.env.field[x, y] == CellType.COLLABORATOR_HEAD:
            pygame.draw.rect(self.screen, Colors.SCREEN_BACKGROUND, cell_coords)                            
            if self.env.collaborator.direction == SnakeDirection.NORTH:
                rotated_icon = self.north_collaborator
            elif self.env.collaborator.direction == SnakeDirection.WEST:
                rotated_icon = self.west_collaborator
            elif self.env.collaborator.direction == SnakeDirection.SOUTH:
                rotated_icon = self.south_collaborator
            else:
                rotated_icon = self.east_collaborator
            self.curr_icon_collaborator = rotated_icon               
            # self.screen.blit(rotated_icon, cell_coords)
            self.last_head_collaborator = self.curr_head_collaborator
            self.curr_head_collaborator = [x,y]
        elif self.env.field[x, y] == CellType.PIT:
            pygame.draw.rect(self.screen, Colors.SCREEN_BACKGROUND, cell_coords)
            self.screen.blit(self.pit_icon, cell_coords)
        elif self.env.field[x, y] == CellType.SNAKE_BODY:
            pygame.draw.rect(self.screen, Colors.SCREEN_BACKGROUND, cell_coords)
            if Point(x,y) in self.env.pit:
                self.screen.blit(self.pit_icon, cell_coords)
        elif self.env.field[x, y] == CellType.COLLABORATOR_BODY:
            pygame.draw.rect(self.screen, Colors.SCREEN_BACKGROUND, cell_coords)
            if Point(x,y) in self.env.pit:
                self.screen.blit(self.pit_icon, cell_coords)
        elif self.env.field[x, y]  == CellType.WALL:
            pygame.draw.rect(self.screen, Colors.SCREEN_BACKGROUND, cell_coords)
            self.screen.blit(self.wall_icon, cell_coords)
        else:
            pygame.draw.rect(self.screen, Colors.SCREEN_BACKGROUND, cell_coords)
            color = Colors.CELL_TYPE[self.env.field[x, y]]
            pygame.draw.rect(self.screen, color, cell_coords, 1)
            # internal_padding = self.CELL_SIZE // 6 * 2
            internal_square_coords = cell_coords.inflate((-self.internal_padding, -self.internal_padding))
            pygame.draw.rect(self.screen, color, internal_square_coords)

    def render(self):
        """ Draw the entire game frame. """
        self.screen.fill(Colors.SCREEN_BACKGROUND)
        num_font = pygame.font.Font(self.base_dir+"fonts/gyparody_tf.ttf", int(24*(self.CELL_SIZE/40.0)))
        if self.collaborating_agent is not None:
            icon_list = [self.good_fruit_icon, self.lava_icon]
            text_fields = ["+"+str(self.env.rewards['good_fruit']), str(self.env.rewards['lava'])]
        else:
            icon_list = [self.good_fruit_icon, self.bad_fruit_icon, self.lava_icon]
            text_fields = ["+"+str(self.env.rewards['good_fruit']), str(self.env.rewards['bad_fruit']), str(self.env.rewards['lava'])]

        for i in range(len(icon_list)):
            icon_list[i] = pygame.transform.scale(icon_list[i], tuple([int(0.8*x) for x in icon_list[i].get_size()]))


        
        if self.collaborating_agent is None:
            text_fields = ["+"+str(self.env.rewards['good_fruit']), str(self.env.rewards['bad_fruit']), str(self.env.rewards['lava'])]
        else:
            self.screen.blit( pygame.transform.scale(self.south, tuple([int(0.8*x) for x in self.south.get_size()]))
                             , ((self.FIELD_SIZE+3.0)*self.CELL_SIZE-self.CELL_SIZE*3//2, self.screen_size[1]//2 - 4.5*self.screen_size[1] // 10))
            self.screen.blit( pygame.transform.scale(self.south_collaborator, tuple([int(0.8*x) for x in self.south_collaborator.get_size()]))
                            , ((self.FIELD_SIZE+3.0)*self.CELL_SIZE-self.CELL_SIZE//2, self.screen_size[1]//2 - 4.5*self.screen_size[1] // 10))
            text_fields = ["+"+str(self.env.rewards['good_fruit'])+'  '+str(self.env.rewards['lava']), 
                          #  str(self.env.rewards['bad_fruit'])+'    '+str(self.env.rewards['bad_fruit']), 
                            str(self.env.rewards['lava'])+'  +'+str(self.env.rewards['good_fruit'])]
        
        ct = 0
        for text in text_fields:
            ct += 1
            disp_num = num_font.render(text, True, (0, 0, 0))
            self.screen.blit(disp_num, ((self.FIELD_SIZE+3.0)*self.CELL_SIZE-disp_num.get_width(), self.screen_size[1]//2 - (4.5-ct)*self.screen_size[1] // 10))
            self.screen.blit(icon_list[ct-1], ((self.FIELD_SIZE+0.5)*self.CELL_SIZE, self.screen_size[1]//2 - (4.5-ct)*self.screen_size[1] // 10))

        for x in range(self.env.field.size):
            for y in range(self.env.field.size):
                self.render_cell(x, y)

    def transition_animation(self, imm_coords, x ,y, x0, y0, reward, curr_icon, interpolate_idx, is_collaborator, imm_coords_collaborator=None):
        
        if not is_collaborator:
            pygame.draw.rect(self.screen, Colors.SCREEN_BACKGROUND, imm_coords)
            if imm_coords_collaborator is not None:
                pygame.draw.rect(self.screen, Colors.SCREEN_BACKGROUND, imm_coords_collaborator)

        imm_coords = pygame.Rect(
            x0*self.CELL_SIZE + (x-x0)*interpolate_idx*self.CELL_SIZE//self.intermediate_frames,
            y0*self.CELL_SIZE + (y-y0)*interpolate_idx*self.CELL_SIZE//self.intermediate_frames,
            self.CELL_SIZE,
            self.CELL_SIZE,
        )
        if self.collaborating_agent is not None:
            if not self.env.in_pit and (x == list(self.env.pit)[0].x and y == list(self.env.pit)[0].y or abs(x - list(self.env.pit)[0].x)== 1 and y == list(self.env.pit)[0].y or abs(y - list(self.env.pit)[0].y)== 1 and x == list(self.env.pit)[0].x ):
                cell_coords = pygame.Rect(
                    list(self.env.pit)[0].x * self.CELL_SIZE,
                    list(self.env.pit)[0].y * self.CELL_SIZE,
                    self.CELL_SIZE,
                    self.CELL_SIZE,
                )
                self.screen.blit(self.pit_icon, cell_coords)

            if self.env.in_pit and x == list(self.env.pit)[0].x and y == list(self.env.pit)[0].y and x0 != x and y0 != y:
                cell_coords = pygame.Rect(
                    list(self.env.pit)[0].x * self.CELL_SIZE,
                    list(self.env.pit)[0].y * self.CELL_SIZE,
                    self.CELL_SIZE,
                    self.CELL_SIZE,
                )
                self.screen.blit(self.pit_icon, cell_coords)

            self.screen.blit(curr_icon, imm_coords)
            if self.env.in_pit and x == list(self.env.pit)[0].x and y == list(self.env.pit)[0].y and interpolate_idx < self.intermediate_frames / 2:
                cell_coords = pygame.Rect(
                    list(self.env.pit)[0].x * self.CELL_SIZE,
                    list(self.env.pit)[0].y * self.CELL_SIZE,
                    self.CELL_SIZE,
                    self.CELL_SIZE,
                )
                self.screen.blit(self.pit_icon, cell_coords)
        else:
            self.screen.blit(curr_icon, imm_coords)
        
        # restore icon from last frame if crashed
        if interpolate_idx < self.intermediate_frames / 3 * 2:
            if reward == self.env.rewards['good_fruit']: # good fruit
                if is_collaborator:
                    cell_coords = pygame.Rect(
                        x * self.CELL_SIZE,
                        y * self.CELL_SIZE,
                        self.CELL_SIZE,
                        self.CELL_SIZE,
                    )
                    self.screen.blit(self.lava_icon, cell_coords)
                else:
                    cell_coords = pygame.Rect(
                        x * self.CELL_SIZE + 5,
                        y * self.CELL_SIZE + 5,
                        self.CELL_SIZE,
                        self.CELL_SIZE,
                    )                           
                    self.screen.blit(self.good_fruit_icon, cell_coords)
            elif reward == self.env.rewards['bad_fruit']:
                cell_coords = pygame.Rect(
                    x * self.CELL_SIZE,
                    y * self.CELL_SIZE,
                    self.CELL_SIZE,
                    self.CELL_SIZE,
                )
                  
                self.screen.blit(self.bad_fruit_icon, cell_coords)
            elif reward == self.env.rewards['lava']:
                if is_collaborator:
                    cell_coords = pygame.Rect(
                        x * self.CELL_SIZE + 5,
                        y * self.CELL_SIZE + 5,
                        self.CELL_SIZE,
                        self.CELL_SIZE,
                    )    
                    self.screen.blit(self.good_fruit_icon, cell_coords)
                else:
                    cell_coords = pygame.Rect(
                        x * self.CELL_SIZE,
                        y * self.CELL_SIZE,
                        self.CELL_SIZE,
                        self.CELL_SIZE,
                    )
                    self.screen.blit(self.lava_icon, cell_coords)
        else:
            if reward == self.env.rewards['good_fruit']:
                if is_collaborator:
                    cell_coords = pygame.Rect(
                        x * self.CELL_SIZE,
                        y * self.CELL_SIZE + 20,
                        self.CELL_SIZE,
                        self.CELL_SIZE*2//3,
                    )
                    self.screen.blit(self.big_crash_icon, cell_coords)
                else:
                    cell_coords = pygame.Rect(
                        x * self.CELL_SIZE + self.CELL_SIZE//2 - self.CELL_SIZE//6,
                        y * self.CELL_SIZE - 10,
                        self.CELL_SIZE,
                        self.CELL_SIZE,
                    )
                    self.screen.blit(self.reward_icon, cell_coords)
            elif reward == self.env.rewards['bad_fruit']:
                cell_coords = pygame.Rect(
                        x * self.CELL_SIZE + 5,
                        y * self.CELL_SIZE + 25,
                        self.CELL_SIZE*2//3,
                        self.CELL_SIZE*2//3,
                    )
                self.screen.blit(self.small_crash_icon, cell_coords)
            elif reward == self.env.rewards['lava']:
                if is_collaborator:
                    cell_coords = pygame.Rect(
                        x * self.CELL_SIZE,
                        y * self.CELL_SIZE + 20,
                        self.CELL_SIZE*3//2,
                        self.CELL_SIZE*3//2,
                    )
                    self.screen.blit(self.accident_icon, cell_coords)
                else:
                    cell_coords = pygame.Rect(
                        x * self.CELL_SIZE,
                        y * self.CELL_SIZE + 20,
                        self.CELL_SIZE,
                        self.CELL_SIZE*2//3,
                    )
                    self.screen.blit(self.big_crash_icon, cell_coords)
        return imm_coords

    def pickup_animation(self, x ,y, reward, is_collaborator):
        if reward == self.env.rewards['good_fruit']: # coin
            if is_collaborator:
                cell_coords = pygame.Rect(
                    x * self.CELL_SIZE,
                    y * self.CELL_SIZE + self.CELL_SIZE//3,
                    self.CELL_SIZE,
                    self.CELL_SIZE*2//3,
                )
                self.screen.blit(self.big_crash_icon, cell_coords)
            else:
                cell_coords = pygame.Rect(
                    x * self.CELL_SIZE + self.CELL_SIZE//2 - self.CELL_SIZE//6,
                    y * self.CELL_SIZE - 10,
                    self.CELL_SIZE,
                    self.CELL_SIZE,
                )    
                self.screen.blit(self.reward_icon, cell_coords)

        elif reward == self.env.rewards['bad_fruit']: #small crash
            cell_coords = pygame.Rect(
                x * self.CELL_SIZE + 5,
                y * self.CELL_SIZE - 5,
                self.CELL_SIZE,
                self.CELL_SIZE,
            )
            self.screen.blit(self.small_crash_icon, cell_coords)

        elif reward == self.env.rewards['lava']: #big crash
            if is_collaborator:
                cell_coords = pygame.Rect(
                    x * self.CELL_SIZE,
                    y * self.CELL_SIZE + self.CELL_SIZE//3,
                    self.CELL_SIZE*3//2,
                    self.CELL_SIZE*3//2,
                )
                self.screen.blit(self.accident_icon, cell_coords)
            else:
                cell_coords = pygame.Rect(
                    x * self.CELL_SIZE,
                    y * self.CELL_SIZE + self.CELL_SIZE//3,
                    self.CELL_SIZE,
                    self.CELL_SIZE*2//3,
                )
                self.screen.blit(self.big_crash_icon, cell_coords)

    def map_key_to_snake_action(self, key):
        """ Convert a keystroke to an environment action. """
        actions = [
            SnakeAction.MAINTAIN_DIRECTION,
            SnakeAction.TURN_LEFT,
            SnakeAction.MAINTAIN_DIRECTION,
            SnakeAction.TURN_RIGHT,
        ]

        key_idx = self.SNAKE_CONTROL_KEYS.index(key)
        direction_idx = ALL_SNAKE_DIRECTIONS.index(self.env.snake.direction)
        return np.roll(actions, -key_idx)[direction_idx]


    def quit_game(self):
        self.env.is_game_over = True
        if self.env.verbose >= 1:
            stats_csv_line = self.env.stats.to_dataframe().to_csv(header=False, index=None)
            print(stats_csv_line, file=self.env.stats_file, end='', flush=True)
        if self.env.verbose >= 2:
            print(self.env.stats, file=self.env.debug_file)
        raise QuitRequestedError

    def handle_pause(self):
        while self.pause:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.pause = False
                        if self.frame_num == 0:
                            pygame.mixer.music.load(self.base_dir+"sound/background1.mp3") 
                            pygame.mixer.music.set_volume(0.4)
                            pygame.mixer.music.play(-1,0.0)
                    if event.key == pygame.K_ESCAPE:
                        self.quit_game()

                if event.type == pygame.QUIT:
                    self.quit_game()


    def run(self, num_episodes=1, participant='test', online_learning=False):

        """ Run the GUI player for the specified number of episodes. """
        pygame.display.update()
        self.fps_clock = pygame.time.Clock()
        if not online_learning:
            if self.collaborating_agent is not None: 
                capture_thread1 = captureThread(0, participant=participant, data_dir='./user_study_data/', exp_id='collaborative', test=self.test)
                capture_thread1.start()
            else:
                capture_thread1 = captureThread(0, participant=participant, data_dir='./user_study_data/', exp_id='original', test=self.test)
                capture_thread1.start()
        try:
            for episode in range(num_episodes):                
                self.run_episode()
                pygame.time.wait(1500)
            if not online_learning: capture_thread1.stop()
        except QuitRequestedError:
            if not online_learning: capture_thread1.stop()

    def run_episode(self):
        """ Run the GUI player for a single episode. """
        
        global frame_ct
        # Initialize the environment.
        self.timestep_watch.reset()
        timestep_result = self.env.new_episode()
        timestep_result_collaborator = timestep_result
        self.agent.begin_episode()

        is_human_agent = isinstance(self.agent, HumanAgent)
        self.timestep_delay = self.HUMAN_TIMESTEP_DELAY if is_human_agent else self.AI_TIMESTEP_DELAY

        """ Select car scheme first """
        if is_human_agent: 
            while not self.selected:
                self.screen.fill(Colors.SCREEN_BACKGROUND)         
                
                small_text_font = pygame.font.Font(self.base_dir+"fonts/gyparody_hv.ttf", int(22*(self.CELL_SIZE/40.0)))  
                car_names = ['Amber','Jade','Ruby']     
                disp_text = self.text_font.render("Select a Vehicle", True, (0, 0, 0))
             
                self.screen.blit(disp_text, (self.screen_size[0]//2 - disp_text.get_width()//2 , self.screen_size[1] // 3 - disp_text.get_height() ))
                
                smaller_text_font = pygame.font.Font(self.base_dir+"fonts/gyparody_hv.ttf", int(16*(self.CELL_SIZE/40.0))) 
                disp_text = smaller_text_font.render("Press <Enter> to confirm", True, (90, 90, 90))    
                self.screen.blit(disp_text, (15 + self.screen_size[0] // 2 - disp_text.get_width()// 2 , self.screen_size[1]*2 // 3 + disp_text.get_height()//2 ))
                
                for scheme_idx in range(len(self.car_schemes)):
                    scheme = self.car_schemes[scheme_idx]
                    car_icon = pygame.transform.scale(pygame.image.load("icon/"+scheme+"_south.png"),(self.CELL_SIZE, self.CELL_SIZE-5))
                    cell_coords = pygame.Rect(
                        self.screen_size[0]//2 - 2*self.CELL_SIZE + scheme_idx*self.CELL_SIZE*2 ,
                        self.screen_size[1] // 2 - self.CELL_SIZE//2,
                        self.CELL_SIZE,
                        self.CELL_SIZE,
                    )    
                    if scheme_idx == self.selected_icon_scheme:
                        pygame.draw.rect(self.screen, Colors.SELECTION, cell_coords)
                    self.screen.blit(car_icon, cell_coords)
                    name_text = small_text_font.render(car_names[scheme_idx], True, (80, 80, 80))
                    cell_coords = pygame.Rect(
                        self.screen_size[0]//2  - 2*self.CELL_SIZE + self.CELL_SIZE//2 - name_text.get_width()//2 + scheme_idx*self.CELL_SIZE*2 ,
                        self.screen_size[1] // 2 + self.CELL_SIZE//2,
                        name_text.get_width(),
                        name_text.get_height(),
                    )
                    self.screen.blit(name_text, cell_coords)
                
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                             self.selected = True
                             #self.pause = False                        
                        elif event.key == pygame.K_RIGHT:
                            self.selected_icon_scheme += 1
                            self.selected_icon_scheme = min(self.selected_icon_scheme,len(self.car_schemes)-1)
                            self.set_icon_scheme(self.selected_icon_scheme)
                        elif event.key == pygame.K_LEFT:
                            self.selected_icon_scheme -= 1
                            self.selected_icon_scheme = max(self.selected_icon_scheme,0)
                            self.set_icon_scheme(self.selected_icon_scheme) 
                        elif event.key == pygame.K_ESCAPE:
                            raise QuitRequestedError
                    if event.type == pygame.QUIT:
                        raise QuitRequestedError
                        
                    
                pygame.display.update()          
                self.fps_clock.tick(20)

            if self.collaborating_agent is not None:
                remaining_schemes = list(range(len(self.car_schemes)))
                remaining_schemes.remove(self.selected_icon_scheme)
                self.selected_icon_scheme_collaborator = random.choice(remaining_schemes)
                self.set_icon_scheme_collaborator(self.selected_icon_scheme_collaborator)
                self.set_fixed_icon_scheme_collaborator()
                
            
            
        self.render()
        start_text_font = pygame.font.Font(self.base_dir+"fonts/gyparody_hv.ttf", int(42*(self.CELL_SIZE/40.0))) 
        disp_text = start_text_font.render("Press <Space> to Start", True, (220, 220, 220))
        self.screen.blit(disp_text, (self.screen_size[0] // 2 - disp_text.get_width()// 2 , self.screen_size[1] // 2 - disp_text.get_height()//2 ))          
        pygame.display.update()
        
                
        

        # Main game loop.
        running = True
        action_selected = False
        while running:          
            frame_ct = self.frame_num
            if not action_selected:
                action = SnakeAction.MAINTAIN_DIRECTION           
                
            # Handle events.
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if is_human_agent and event.key in self.SNAKE_CONTROL_KEYS:
                        action = self.map_key_to_snake_action(event.key)
                    if event.key == pygame.K_SPACE:
                        self.pause = True
                        
                    if event.key == pygame.K_ESCAPE:
                        self.quit_game()

                if event.type == pygame.QUIT:
                    self.quit_game()

            self.handle_pause()

            # Initial sound
            if self.frame_num == 0 and PLAY_SOUND:
                self.begin_sound.play()

            if self.last_head == [0,0]:
                for interpolate_idx in range(4): 
                    cell_coords = pygame.Rect(
                        self.env.snake.head[0]*self.CELL_SIZE,
                        self.env.snake.head[1]*self.CELL_SIZE,
                        self.CELL_SIZE,
                        self.CELL_SIZE,
                    )
                    self.screen.blit(self.spawn_icon, cell_coords)

                    if self.collaborating_agent is not None:
                        cell_coords_collaborator = pygame.Rect(
                            self.env.collaborator.head[0]*self.CELL_SIZE,
                            self.env.collaborator.head[1]*self.CELL_SIZE,
                            self.CELL_SIZE,
                            self.CELL_SIZE,
                        )                    
                        self.screen.blit(self.spawn_icon, cell_coords_collaborator)

                    self.render_scoreboard(0, self.env.max_step_limit, 0)
                    pygame.display.update()
                    self.fps_clock.tick(self.intermediate_frames+5)
                pygame.draw.rect(self.screen, Colors.SCREEN_BACKGROUND, cell_coords)
                if self.collaborating_agent is not None:
                    pygame.draw.rect(self.screen, Colors.SCREEN_BACKGROUND, cell_coords_collaborator)

            # Update game state.
            timestep_timed_out = self.timestep_watch.time() >= self.timestep_delay
            human_made_move = is_human_agent and action != SnakeAction.MAINTAIN_DIRECTION
                    
            if timestep_timed_out or human_made_move:
                self.timestep_watch.reset()
                self.frame_num = self.frame_num + 1
                self.sound_played = False
                
                if not is_human_agent:
                    action = self.agent.act(timestep_result.observation, timestep_result.reward)
                elif self.collaborating_agent is not None:
                    try:
                        # collaborator_action = self.collaborating_agent.act(timestep_result_collaborator.observation, timestep_result_collaborator.reward)
                        collaborator_action = self.collaborating_agent.act(timestep_result.observation, timestep_result_collaborator.reward)
                    except:
                        smaller_text_font = pygame.font.Font(self.base_dir+"fonts/gyparody_hv.ttf", int(36*(self.CELL_SIZE/40.0))) 
                        disp_text = smaller_text_font.render("Round Finished", True, (220, 220, 220))    
                        self.screen.blit(disp_text, (15 + self.screen_size[0] // 2 - disp_text.get_width()// 2 , self.screen_size[1]*2 // 3 + disp_text.get_height()//2 ))
                        pygame.display.update()
                        time.sleep(2)
                        self.agent.end_episode()
                        running = False
                
                self.env.choose_action(action)
                if self.collaborating_agent is not None:
                    self.env.choose_action_collaborator(collaborator_action)

                action_selected = False
                
                if self.collaborating_agent is not None:
                    if self.collaborating_agent_name == 'mixed':
                        timestep_result, timestep_result_collaborator = self.env.timestep_team(self.punch_sound, self.good_sound, self.bad_sound, self.very_bad_sound, self.stuck_sound, self.free_sound, self.collaborating_agent.curr_agent)
                    else:
                        timestep_result, timestep_result_collaborator = self.env.timestep_team(self.punch_sound, self.good_sound, self.bad_sound, self.very_bad_sound, self.stuck_sound, self.free_sound)
                else:
                    if self.agent_name == 'mixed':
                        timestep_result = self.env.timestep(self.punch_sound, self.good_sound, self.bad_sound, self.very_bad_sound, self.free_sound, self.agent.curr_agent)
                    else:
                        timestep_result = self.env.timestep(self.punch_sound, self.good_sound, self.bad_sound, self.very_bad_sound, self.free_sound)

                if self.save_frames:
                    if self.agent_name == 'a2c':
                        for a in range(3):                    
                            qval = self.agent.get_q_value(timestep_result.observation, a)
                            pygame.image.save(self.screen, 'screenshots/frame-%03d_%02d_%.3f.png' % (self.frame_num, a, qval))
                    else:
                        pygame.image.save(self.screen, 'screenshots/frame-%03d.png' % (self.frame_num))

                if timestep_result.is_episode_end:
                    
                    smaller_text_font = pygame.font.Font(self.base_dir+"fonts/gyparody_hv.ttf", int(36*(self.CELL_SIZE/40.0))) 
                    disp_text = smaller_text_font.render("Round Finished", True, (220, 220, 220))    
                    self.screen.blit(disp_text, (15 + self.screen_size[0] // 2 - disp_text.get_width()// 2 , self.screen_size[1]*2 // 3 + disp_text.get_height()//2 ))
                    pygame.display.update()
                    time.sleep(2)
                    self.agent.end_episode()
                    running = False
                 
                if self.collaborating_agent is not None and timestep_result_collaborator.is_episode_end:
                    
                    smaller_text_font = pygame.font.Font(self.base_dir+"fonts/gyparody_hv.ttf", int(36*(self.CELL_SIZE/40.0))) 
                    disp_text = smaller_text_font.render("Round Finished", True, (220, 220, 220))    
                    self.screen.blit(disp_text, (15 + self.screen_size[0] // 2 - disp_text.get_width()// 2 , self.screen_size[1]*2 // 3 + disp_text.get_height()//2 ))
                    pygame.display.update()
                    time.sleep(2)
                    self.agent.end_episode()
                    running = False

            # Render.
            if running:  
                self.render()

                if SNAKE_GROW:
                    score = self.env.snake.length - self.env.initial_snake_length
                else:
                    if self.collaborating_agent is not None: score = self.env.stats.sum_episode_rewards + self.env.stats_collaborator.sum_episode_rewards
                    else:  score = self.env.stats.sum_episode_rewards      
                
                # transition animation
                time_remaining = self.env.max_step_limit-self.env.timestep_index
                x, y = self.curr_head
                         
                x0, y0 = self.last_head  
                imm_coords = pygame.Rect(
                    x0*self.CELL_SIZE,
                    y0*self.CELL_SIZE,
                    self.CELL_SIZE,
                    self.CELL_SIZE,
                )

                if self.collaborating_agent is not None:
                    x_collaborator, y_collaborator = self.curr_head_collaborator
                             
                    x0_collaborator, y0_collaborator = self.last_head_collaborator 
                    imm_coords_collaborator = pygame.Rect(
                        x0_collaborator*self.CELL_SIZE,
                        y0_collaborator*self.CELL_SIZE,
                        self.CELL_SIZE,
                        self.CELL_SIZE,
                    )

                for interpolate_idx in range(1,self.intermediate_frames-1):

                    for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN:
                            if is_human_agent and event.key in self.SNAKE_CONTROL_KEYS:
                                action = self.map_key_to_snake_action(event.key)
                                action_selected = True
                            if event.key == pygame.K_SPACE:
                                self.pause = True
                            if event.key == pygame.K_ESCAPE:
                                self.quit_game()

                        if event.type == pygame.QUIT:
                            self.quit_game()

                    self.handle_pause()
  
                    if self.collaborating_agent is not None:
                        imm_coords = self.transition_animation(imm_coords, x ,y, x0, y0, timestep_result.reward, self.curr_icon, interpolate_idx, False, imm_coords_collaborator)
                        imm_coords_collaborator = self.transition_animation(imm_coords_collaborator, x_collaborator ,y_collaborator, x0_collaborator, y0_collaborator, timestep_result_collaborator.reward, self.curr_icon_collaborator, interpolate_idx, True) 
                    else:
                        imm_coords = self.transition_animation(imm_coords, x ,y, x0, y0, timestep_result.reward, self.curr_icon, interpolate_idx, False)

                    if self.collaborating_agent is not None: 
                        self.render_scoreboard(score, time_remaining, timestep_result.reward + timestep_result_collaborator.reward)
                    else: 
                        self.render_scoreboard(score, time_remaining, timestep_result.reward )
                    pygame.display.set_caption(f'Robotaxi [Score: {score:01d}]   |   [Steps Remaining: {time_remaining:01d}]')                    
                    pygame.display.update()
                    self.fps_clock.tick(self.intermediate_frames+5)
               
                pygame.draw.rect(self.screen, Colors.SCREEN_BACKGROUND, imm_coords)
                
                # final pose
                cell_coords = pygame.Rect(
                    x*self.CELL_SIZE,
                    y*self.CELL_SIZE,
                    self.CELL_SIZE,
                    self.CELL_SIZE,
                )
                self.screen.blit(self.curr_icon, cell_coords)

                # Pick up item animation
                self.pickup_animation(x, y, timestep_result.reward, False)
                if self.collaborating_agent is not None:
                    self.pickup_animation(x_collaborator, y_collaborator, timestep_result_collaborator.reward, True)
                
                time_remaining = self.env.max_step_limit-self.env.timestep_index

                pygame.display.set_caption(f'Robotaxi [Score: {score:01d}]   |   [Steps Remaining: {time_remaining:01d}]')
                if self.collaborating_agent is not None: 
                    self.render_scoreboard(score, time_remaining, timestep_result.reward +  timestep_result_collaborator.reward)
                else: 
                    self.render_scoreboard(score, time_remaining, timestep_result.reward )
                pygame.display.update()
                self.fps_clock.tick(self.FPS_LIMIT)


class Stopwatch(object):
    """ Measures the time elapsed since the last checkpoint. """

    def __init__(self):
        self.start_time = pygame.time.get_ticks()

    def reset(self):
        """ Set a new checkpoint. """
        self.start_time = pygame.time.get_ticks()

    def time(self):
        """ Get time (in milliseconds) since the last checkpoint. """
        return pygame.time.get_ticks() - self.start_time


class Colors:

    SCREEN_BACKGROUND = (119, 119, 119)
    SCORE = (120, 100, 84)
    SCORE_GOOD =  (50, 205, 50)
    SCORE_BAD =  (255, 255, 33)
    SCORE_VERY_BAD =  (205, 20, 50)
    SELECTION = (215, 215, 215)
    CELL_TYPE = {
        CellType.WALL: (26, 26, 26),
        CellType.SNAKE_BODY: (82, 154, 255),
        CellType.SNAKE_HEAD: (65, 132, 255),
        CellType.GOOD_FRUIT: (85, 242, 240),
        CellType.BAD_FRUIT: (177, 242, 85),
        CellType.LAVA: (150, 53, 219),
        CellType.PIT: (179, 179, 179),
    }

class QuitRequestedError(RuntimeError):
    """ Gets raised whenever the user wants to quit the game. """
    pass
