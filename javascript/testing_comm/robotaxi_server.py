# docs @ http://flask.pocoo.org/docs/1.0/quickstart/

from flask import Flask, jsonify, request, render_template
import requests as req
import subprocess
import mysql.connector
import os
import json
import random
import numpy as np
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'storage/'
json_file = json.loads('{  "field": [    "########",    "#......#",    "#...S..#",    "#......#",    "#.P....#",    "#...C..#",    "#......#",    "########"  ],  "initial_snake_length": 1,  "max_step_limit": 200,  "rewards": {    "timestep": 0,    "good_fruit": 6,    "bad_fruit": -1,    "died": 0,    "lava": -5  }}')

def random_generate(character):
    temp_bool = False

    while (temp_bool):
        rand1 = math.floor(math.rand() * math.floor(len(json_file['field'][0])))
        rand2 = math.floor(math.rand() * math.floor(len(json_file['field'])))
        if map[rand1][rand2] == '.':
            map[rand1][rand2] = character
            temp_bool = True
    return

def create_snake(startx, starty):
    for z in range (0, dots):
        x[z] = startx - (z * DOT_SIZE)
        y[z] = starty
        orientation[z] = 3;

dots = json_file['initial_snake_length']
NUM_OBJ = 2
adding_obj = []

cycles = 0
score = 0

left_direction = False;
right_direction = True;
up_direction = False;
down_direction = False;
go = True;

DELAY = 75;
C_HEIGHT = 700;
C_WIDTH = 700;
DOT_SIZE = C_HEIGHT / len(json_file['field'][0]);
MAX_DOTS = len(json_file['field'][0]) * len(json_file['field'])
INC_VAL = 10
COLLISION_TIME = 7;
RANDGEN_TIME = -1 * (COLLISION_TIME + 3);

x = [0] * MAX_DOTS
y = [0] * MAX_DOTS
orientation = [0] * MAX_DOTS
game_map = ['.'] * len(json_file['field'])
accident_tracker = [0] * len(json_file['field'])
next_transition = [1.0, 0.0]

for i in range (0, len(json_file['field'])):
    game_map[i] = list(json_file['field'][i])
    accident_tracker[i] = [0] * len(json_file['field'][0])

transition = [None] * MAX_DOTS
    
for i in range (0, len(transition)):
    if i == 0:
        transition[i] = [1, 0]
    else :
        transition[i] = [1, 0]

temp = [['C', 0], ['P', 0], ['B', 0]]

for i in range (0, len(json_file['field'][0])):
    for j in range (0, len(json_file['field'])):
        if game_map[i][j] == 'S':
            game_map[i][j] = '.'
            create_snake(i * DOT_SIZE, j * DOT_SIZE)
        elif game_map[i][j] != '.' and game_map[i][j] != '#':
            for k in range (0, len(temp)):
                if temp[k][0] == game_map[i][j]:
                    temp[k][1] += 1

for i in range (0, len(temp)):
    for k in range(temp[i][1], NUM_OBJ):
        random_generate(temp[i][0])



@app.route('/init', methods=['GET'])
def initialize():
    message = {
        'C_WIDTH': C_WIDTH,
        'C_HEIGHT': C_HEIGHT,
        'score': score,
        'cycle': cycles,
        'max_cycle': json_file['max_step_limit']
    }
    return jsonify(message)
            
@app.route('/render', methods=['GET'])
def render():
    message = {'greeting':'Hello from Flask!'}
    return jsonify(message)  # serialize and use JSON headers
    

@app.route('/inputs', methods=['POST'])
def recieve_inputs():

    # POST request
    req_data = request.get_json()

    # Javascript has returned a json. parse through
    # Probably user input, video/audio raw data

    # RL/Pytorch

    # Process outputs back into correct states/actions (JSON)

    #return

    return 'OK', 200

@app.route('/finish', methods=['POST'])
def finish():

    # Store the video file recieved
    if request.method == 'POST':

        # Connect to the localhost database
        mydb = mysql.connector.connect(
            host="localhost",
            db="robotaxi",
            user="root",
            password="Mturk$35@"
        )

        # Get the correct data to send to database
        cursor = mydb.cursor()
        sql_insert_blob_query = """ INSERT INTO player (player_id, video) VALUES (%s, %s)"""

        player_id = random.randint(10000, 99999)
        video_file = request.files['video-blob']
        #insert_blob_tuple = (player_id, video_file)
        #result = cursor.execute(sql_insert_blob_query, insert_blob_tuple)
        video_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'testing_audio.webm'))
        
        #mydb.commit()

        #with open ('testing.webm', 'wb') as f_output:
            #f_output.write(video_file.stream)

        # if the connection exists, end the connection
        if mydb.is_connected():
            cursor.close()
            mydb.close()
        
        return 'finished?'
    else:
        return "ERROR: Only POST requests allowed for /finish"

    
@app.route('/', methods=['GET', 'POST'])
def page():

    #Fire up the javascript page
    return render_template('robotaxi_game.html')
