# follow.py
#
# Follow a file like tail -f.
import sys, os
from os import listdir
from os.path import isfile, isdir, join
import numpy as np
import time
import subprocess

import torch
from network_facs import Net
from torch.autograd import Variable

import threading


feature_indexes = [4, 696, 697, 698, 699, 700, 701, 702, 703, 704, 705, 706, 707, 708, 709, 710, 711, 712, 713, 679, 680, 681, 682, 683, 684, 685, 686, 687, 688, 689, 690, 691, 692, 693, 694, 695, 293, 294, 295, 296, 297, 298]

imgwindow_size = 50
buffer_size = 5
feature_size =  512 + 61 + 35 + 54 + 40 + 10

frames_pre = 4
frames_after = 18 
window_size = frames_pre + frames_after + 1
detectionwindow_size = window_size

num_classes1 = 3
num_classes2 = window_size * 10

model_dir = './online_learning_reward_models/' 
data_dir = "./openface_out/" 

curr_feature_out = None

class FeedbackDetector(threading.Thread):
    # Fixed Parameters
     #feature_columns = ['success', 'AU01_c', 'AU02_c', 'AU04_c', 'AU05_c', 'AU06_c', 'AU07_c', 'AU09_c', 'AU10_c', 'AU12_c', 'AU14_c', 'AU15_c', 'AU17_c', 'AU20_c', 'AU23_c', 'AU25_c', 'AU26_c', 'AU28_c', 'AU45_c',  'AU01_r', 'AU02_r', 'AU04_r', 'AU05_r', 'AU06_r', 'AU07_r', 'AU09_r', 'AU10_r', 'AU12_r', 'AU14_r', 'AU15_r', 'AU17_r', 'AU20_r', 'AU23_r', 'AU25_r', 'AU26_r', 'AU45_r', 'pose_Tx', 'pose_Ty', 'pose_Tz', 'pose_Rx', 'pose_Ry', 'pose_Rz']
      

    def __init__(self, participant_id):
        super(FeedbackDetector, self).__init__()

        self.detectionwindow = []
        self.processed_data = [] 
        self.roll = None
        self.pitch = None
        self.yaw = None 
        self.avg_head_pose = None
        self.head_nod = []
        self.head_shake = []
        self.participant_id = participant_id
        
        all_models = [join(model_dir, f) for f in os.listdir(model_dir) if isfile(join(model_dir, f))]
        best_model = None
        lowest_loss = 100.0

        for model_path in all_models:
            model_info = model_path.replace('.pkl', '')
            model_info = model_info.split('/')[-1].split('_')

            if not model_info[0] == 'facsposeauxall': continue
            loss = float(model_info[-1])
            
            if loss < lowest_loss:
                lowest_loss = loss
                best_model = model_path

        if best_model is None: 
            print('No model found in', model_dir)
                           
        self.net = Net(input_size=feature_size, num_classes1=num_classes1, num_classes2=num_classes2, apply_event_mask=False, window_size=window_size)
        self.net.load_state_dict(torch.load(best_model))
        self.net.eval()
        self.net.cuda()


    def follow(self, thefile):
        thefile.seek(0,2)
        while True:
            line = thefile.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line


    def run(self):
        global curr_feature_out
        print('START RUNNING')
        feature_data_file = None
        data_files = [join(data_dir+self.participant_id,f) for f in listdir(data_dir+self.participant_id)]
        #print(data_files)
        for data_file in data_files:
            if data_file.endswith('.csv'):
                feature_data_file = data_file
                break        
        data_ct = 0
        logfile = open(feature_data_file,"r")           
        loglines = self.follow(logfile)
        detections = []
        for line in loglines:            
            line_data = [float(num) for num in line.strip().split(',')]           
            feat_data = [line_data[feature_index] for feature_index in feature_indexes]            
            if feat_data[0] == 0 and len(self.processed_data) > 0: # no face detected
                    self.processed_data.append(self.processed_data[-1])
                    while len(self.processed_data) > buffer_size: self.processed_data.pop(0)
                    continue

            orig_feat = np.array(feat_data[1:36])      
            pose_feat = np.zeros((2+26*2,))        
            
            if self.avg_head_pose is None:
                self.avg_head_pose = [np.array(feat_data[-6:])]
            elif data_ct < 25:
                self.avg_head_pose.append(np.array(feat_data[-6:]))            
                        
            head_pose = np.array(feat_data[-6:]) - np.mean(self.avg_head_pose, axis=0)

            if self.roll is None: self.roll = [head_pose[3]] * imgwindow_size
            else: self.roll[data_ct%imgwindow_size] = head_pose[3]
            if self.pitch is None: self.pitch = [head_pose[4]] * imgwindow_size
            else: self.pitch[data_ct%imgwindow_size] = head_pose[4]
            if self.yaw is None: self.yaw = [head_pose[5]] * imgwindow_size
            else: self.yaw[data_ct%imgwindow_size] = head_pose[5]

            self.head_nod.append((head_pose[3]-np.mean(self.roll))) #**2 10.0*
            self.head_shake.append((head_pose[4]-np.mean(self.pitch))) #**2 10.0*
       
            if len(self.head_nod) > imgwindow_size: self.head_nod = self.head_nod[-imgwindow_size:]
            dfft_nod = np.real(np.fft.rfft(self.head_nod))
            if len(self.head_shake) > imgwindow_size: self.head_shake = self.head_shake[-imgwindow_size:]
            dfft_shake = np.real(np.fft.rfft(self.head_shake))

            pose_feat[0] = (self.head_nod[-1]**2)*10.0
            pose_feat[1] = (self.head_shake[-1]**2)*10.0
            pose_feat[2:2+dfft_nod.shape[0]] = dfft_nod
            pose_feat[2+26:2+26+dfft_shake.shape[0]] = dfft_shake
            combo_feat = np.concatenate((orig_feat,pose_feat))
            
            self.processed_data.append(np.array(combo_feat))
            while len(self.processed_data) > buffer_size: self.processed_data.pop(0)

            dframe_data = np.max(self.processed_data, axis=0)
            
            facs_r_feat = dframe_data[18:35]
            dframe_data[18:35] = np.where(facs_r_feat>=1,1,0)                     
            
            #print(data_ct, dframe_data,)
            feature_data = np.zeros((feature_size,))
            feature_data[512 + 61 : 512 + 61 + 35 + 54 ] = dframe_data
            
            self.detectionwindow.append(np.array(feature_data))
            while len(self.detectionwindow) > detectionwindow_size: 
                self.detectionwindow.pop(0)
            
            data_ct += 1

            if len(self.detectionwindow) == detectionwindow_size:
                
                net_input = torch.Tensor(np.array([self.detectionwindow]))
                net_input = Variable(net_input.float()).cuda()
                #print(net_input[0][0][512+61+35:512+61+35+54])
                outputs, _ = self.net(net_input, None)      
                outputs = outputs.cpu().data.float()
                p = [float(num) for num in (torch.exp(outputs)/torch.sum(torch.exp(outputs))).cpu().data[0]]
                #print(data_ct // 5, p)
                detections.append(list(p))
                #print(detections)
                while len(detections) > 4: detections.pop(0)
                if len(detections) == 4: curr_feature_out = list(np.mean(detections,axis=0))
                #print(data_ct, curr_feature_out)
                #print(dframe_data[0])
                #print(round(pose_feat[0],2), round(pose_feat[1],2))

    def peek(self):
        global curr_feature_out
        while curr_feature_out is None: pass
        return curr_feature_out


    def stop(self):
        self._stop_event.set()

if __name__ == '__main__':

    import matplotlib.pyplot as plt
    proc = subprocess.Popen(['/bin/bash','../../start_openface.bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    detector = FeedbackDetector()
    detector.start()
    
    x_pos = [0,1,2]
    x = ["-5","-1","6"]
    while True:
        plt.cla()
        time.sleep(1)
        p = detector.peek()
        print(p)
        plt.ylabel("Reward Category")
        plt.xlabel("Model Output as Probability (Score)")
        plt.barh(x_pos, p)                
        plt.yticks(x_pos, x)
        plt.xlim(0,1.0)
        plt.pause(0.0001)
    
