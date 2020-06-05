import glob
import os
import time
from os import listdir
from os.path import isfile, join
from keras.utils import to_categorical
import numpy as np

def parse_file(log_file_handle):
    log_data = []
    line_ct = 0
    frame_data = []

    total_reward = 0
    scores = []
    rewards = []
    actions = []

    for line in log_file_handle:
        if line.startswith('6'):
            frame_data.append(line)
            line_ct += 1
            
        if line.startswith('R'):
            total_reward = total_reward + eval(line.strip().split('=')[1])
            scores.append(total_reward)
            rewards.append(eval(line.strip().split('=')[1]))

        if line.startswith('action'):
            actions.append(eval(line.strip().split(':')[1]))

        if line_ct == 20:
            line_ct = 0
            obs_data = [[int(ch) for ch in line.strip()] for line in frame_data]
            frame = to_categorical(list(obs_data))
            frame = np.moveaxis(frame, -1, 0)
            log_data.append(frame)
            frame_data = []
            
    return log_data, rewards, actions, scores



def generate_demonstrations(demo_dir='./demos'):
    demo_files = [join(demo_dir, f) for f in listdir(demo_dir) if isfile(join(demo_dir, f))]
    demo_rollouts = []
    rollout_ct = 0
    for file_path in demo_files:
        demo_rollouts.append([])
        curr_file = open(file_path)
        log_data, rewards, actions, scores = parse_file(curr_file)
        print(rollout_ct,file_path,scores[-1],actions[0])
        for i in range(1,len(log_data)):
            demo_rollouts[-1].append((log_data[i],actions[i]))
        rollout_ct += 1
    return (demo_rollouts)
    

def main():
    demo_rollouts = generate_demonstrations()
    print(len(demo_rollouts),len(demo_rollouts[0]))

if __name__ == "__main__":
    main()
