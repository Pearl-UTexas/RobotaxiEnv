# export FLASK_APP=robotaxi_server.py
# flask run

from flask import Flask, jsonify, request, render_template, abort
import requests as req
import subprocess
import mysql.connector
import os
import json
import random
import numpy as np
import base64
import random
import string
from robogame import RoboTaxi

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'storage/'
global all_games
all_games = dict()

@app.route('/init', methods=['POST'])
def initialize():
    req_data = request.get_json(force=True)

    # check if the key for the game is present
    if all_games.get(req_data['key']) == None:
        abort(404, "Game unique key not found. Please refresh the page")
    else :
        # if so, return the initial game parameters
        game = all_games[req_data['key']]
        return jsonify(game.initial_parameters())
            
@app.route('/render', methods=['POST'])
def render():
    req_data = request.get_json(force=True)

    # check if the key for the game is present
    if all_games.get(req_data['key']) == None:
        abort(404, "Game unique key not found. Please refresh the page")
    else :
        # if so, get this time's render arguments
        game = all_games[req_data['key']]
        return jsonify(game.get_render())  # serialize and use JSON headers

@app.route('/inputs', methods=['POST'])
def recieve_inputs():

    # check if the key is within the scope
    req_data = request.get_json(force=True)
    if all_games.get(req_data['key']) == None:
        abort(404, "Game unique key not found. Please refresh the page")
    
    game = all_games[req_data['key']]
    # if so, update the arguments based off of the transition
    game.update(req_data['next_transition'])

    # Javascript has returned a json. parse through
    # Probably user input, video/audio raw data

    # RL/Pytorch

    # Process outputs back into correct states/actions (JSON)

    #return

    return jsonify({"BLANK" : "TEMP"})

@app.route('/finish', methods=['POST'])
def finish():

    # Store the video file recieved
    key = request.form.get('key');

    # check if the game key is present
    if all_games.get(key) == None:
        abort(404, "Game unique key not found. Please refresh the page")
    game = all_games[key]

    # store the video file on local disk
    video_file = request.files['video-blob']
    video_file.save(os.path.join(app.config['UPLOAD_FOLDER'], key + '.webm'))

    # # Connect to the localhost database
    # mydb = mysql.connector.connect(
    #     host="localhost",
    #     db="robotaxi",
    #     user="root",
    #     password="Mturk$35@"
    # )
    
    # store the video file and other data on a database
    #cursor = mydb.cursor()
    #sql_insert_blob_query = """ INSERT INTO player (player_id, video) VALUES (%s, %s)"""
    #insert_blob_tuple = (player_id, video_file)
    #result = cursor.execute(sql_insert_blob_query, insert_blob_tuple)
    #mydb.commit()

    # if the connection exists, end the connection
    # if mydb.is_connected():
    #     cursor.close()
    #     mydb.close()
    
    return 'finished?'

def ran_gen(size, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))
    
@app.route('/', methods=['GET', 'POST'])
def page():
    key = ran_gen(16, "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")
    all_games[key] = RoboTaxi()
    print(key)
    #Fire up the javascript page
    return render_template('robotaxi_game.html', key=key)
