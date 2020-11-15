# Robotaxi User Study Environment
(Game Logic Modified from repository: [snake-ai-reinforcement](https://github.com/YuriyGuts/snake-ai-reinforcement))


![robotaxi_env](https://github.com/yuchen93/RoboTaxi/blob/master/.robotaxi_env.jpg)

## Requirements

- Recommanded: [install anaconda](https://docs.anaconda.com/anaconda/install/)
- Python 3.6 or above. 
- Install all Python dependencies, run:
```
$ python3 -m pip install --upgrade -r requirements.txt
```

## Play Robotaxi

The behavior of the agent can be tested either in batch CLI mode where the agent plays a set of episodes and outputs summary statistics, or in GUI mode where you can see each individual step and action.

To test the agent in batch CLI mode, run the following command and check the generated **.csv** file:
```
$ python3 play.py --agent mixed --interface cli --num-episodes 100 [--level robotaxi/levels/8x8-blank.json] 
```

To use the GUI mode, run:
```
$ python3 play.py --agent mixed [--interface gui --level robotaxi/levels/8x8-blank.json --num-episodes 1]
```

To play on your own using the arrow keys, run:
```
$ python3 play.py --agent human [--interface gui --level robotaxi/levels/8x8-blank.json --num-episodes 1]
```


## Data collection script

Script to play back recordings for collection human reactions (different condition number corresponds to different episode):
```
python start_data_collection.py --cond [0,1,..,5] 
```

## Playback Recordings

To playback recorded behavior (use --save_frames to save individual game frames as images):
```
python render_from_log.py --log_file <log_file_name> [--original] [--save_frames]
```


