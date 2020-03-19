#!/usr/bin/env python3

"""
Parses 20*20 Grids with 4 indicating walls
"""
import sys, os
import random
import argparse



def parse_command_line_args(args):
    """ Parse command-line arguments and organize them into a single structured object. """

    parser = argparse.ArgumentParser(
        description='Parse log into individual episodes.'
    )

    parser.add_argument(
        '--log_file', 
        required=True,
        type=str, 
        help='log file name'
    )

    parser.add_argument(
        '--num-episodes', 
        required=True,
        type=int, 
        help='number of episodes'
    )
    return parser.parse_args(args)


def main():
    parsed_args = parse_command_line_args(sys.argv[1:])

    directory = parsed_args.log_file.split('.')[0]
    if not os.path.exists(directory):
        os.makedirs(directory)

    episode_ct = 0
    line_ct = 0
    log_file_handle = open(parsed_args.log_file, 'r')
    episode_file_handle = open(directory+'/episode_'+str(episode_ct)+'.record', 'w')
    print(parsed_args.num_episodes)
    for line in log_file_handle:
        episode_file_handle.write(line)
        if line.startswith('max_step_limit'):
            max_step_limit_line = line
        
        if line.strip().endswith('}'):
            print('episode:',episode_ct,' at line:',line_ct)
            episode_ct += 1
            episode_file_handle.close()
            if episode_ct < parsed_args.num_episodes:
                episode_file_handle = open(directory+'/episode_'+str(episode_ct)+'.record', 'w')
                episode_file_handle.write(max_step_limit_line)
        line_ct += 1
    log_file_handle.close()

if __name__ == '__main__':
    main()

