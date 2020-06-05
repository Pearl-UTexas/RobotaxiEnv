import argparse
import os
# workaround to unpickle olf model files
import sys

import numpy as np
import torch

from a2c_ppo_acktr.envs import VecPyTorch, make_vec_envs
from a2c_ppo_acktr.utils import get_render_func, get_vec_normalize

sys.path.append('a2c_ppo_acktr')

parser = argparse.ArgumentParser(description='RL')
parser.add_argument(
    '--seed', type=int, default=1, help='random seed (default: 1)')
parser.add_argument(
    '--log-interval',
    type=int,
    default=20,
    help='log interval, one log per n updates (default: 10)')
parser.add_argument(
    '--env-name',
    default='snake',
    help='environment to train on (default: snake)')
parser.add_argument(
    '--load-dir',
    default='./trained_models/a2c/',
    help='directory to save agent logs (default: ./trained_models/ppo/)')
parser.add_argument(
    '--non-det',
    action='store_true',
    default=False,
    help='whether to use a non-deterministic policy')
args = parser.parse_args()

args.det = not args.non_det

env = make_vec_envs(
    args.env_name,
    args.seed + 1000,
    1,
    None,
    None,
    device='cpu',
    allow_early_resets=False)

# Get a render function
render_func = get_render_func(env)

# We need to use the same statistics for normalization as used in training
actor_critic, ob_rms = \
            torch.load(os.path.join(args.load_dir, args.env_name + ".pt"))

#print(ob_rms.mean, ob_rms.var)

vec_norm = get_vec_normalize(env)

if vec_norm is not None:
    vec_norm.eval()
    vec_norm.ob_rms = ob_rms

recurrent_hidden_states = torch.zeros(1,
                                      actor_critic.recurrent_hidden_state_size)
masks = torch.zeros(1, 1)


if render_func is not None:
    render_func('human')

if args.env_name.find('Bullet') > -1:
    import pybullet as p

    torsoId = -1
    for i in range(p.getNumBodies()):
        if (p.getBodyInfo(i)[0].decode() == "torso"):
            torsoId = i


returns = []
for itr in range(50):

    obs = env.reset()
    done = False
    step_ct = 0
    totla_reward = 0

    while not done:
        with torch.no_grad():
            #print(obs)
            value, action, _, recurrent_hidden_states = actor_critic.act(
                obs.cuda(), recurrent_hidden_states, masks, deterministic=args.det)
            #print(' - step:', step_ct,', action:', action[0], ', value:', value[0] )

        # Obser reward and next obs
        obs, reward, done, _ = env.step(action)
        #print(obs)
        step_ct += 1
        #print('   reward:',reward)
        totla_reward += reward
        masks.fill_(0.0 if done else 1.0)

        if args.env_name.find('Bullet') > -1:
            if torsoId > -1:
                distance = 5
                yaw = 0
                humanPos, humanOrn = p.getBasePositionAndOrientation(torsoId)
                p.resetDebugVisualizerCamera(distance, yaw, -20, humanPos)

        if render_func is not None:
            render_func('human')
            
    print('itr', itr + 1 , ' return:',totla_reward)
    returns.append(totla_reward)
print(np.mean(returns),'+-',np.std(returns))
