# export FLASK_APP=robotaxi_server.py
# flask run
# aws configure (command to change the key id, secret key, or region)

from flask import Flask, jsonify, request, render_template, abort, session
from flask_session import Session
import requests as req
import subprocess
#import mysql.connector
import os
import json
import random
import numpy as np
import base64
import random
import string
from robogame import RoboTaxi
import boto3

app = Flask(__name__)
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

@app.route('/init', methods=['POST'])
def initialize():
    req_data = request.get_json(force=True)

    print("Session dict: " + str(session))

    # check if the key for the game is present
    if session[req_data['key']] == None:
        print('404 key not found')
        abort(404, "Game unique key not found. Please refresh the page")
    else :
        # if so, return the initial game parameters
        game = session[req_data['key']]
        return jsonify(game.initial_parameters())
            
@app.route('/render', methods=['POST'])
def render():
    req_data = request.get_json(force=True)
    # check if the key for the game is present
    if session[req_data['key']] == None:
        abort(404, "Game unique key not found. Please refresh the page")
    else :
        # if so, get this time's render arguments
        game = session[req_data['key']]
        return jsonify(game.get_render())  # serialize and use JSON headers

@app.route('/inputs', methods=['POST'])
def recieve_inputs():
    # check if the key is within the scope
    req_data = request.get_json(force=True)

    if session[req_data['key']] == None:
        abort(404, "Game unique key not found. Please refresh the page")

    game = session[req_data['key']]
    # if so, update the arguments based off of the transition
    game.update(req_data['next_transition'])

    # Javascript has returned a json. parse through
    # Probably user input, video/audio raw data

    # RL/Pytorch

    # Process outputs back into correct states/actions (JSON)

    #return

    return jsonify({"BLANK" : "TEMP"})


# @app.route('/finish', methods=['POST'])
# def finish():
# 
#     # Store the video file recieved
#     key = request.form.get('key');
# 
#     # check if the game key is present
#     if session[req_data['key']] == None:
#         abort(404, "Game unique key not found. Please refresh the page")
#     game = session[req_data['key']]
# 
#     # store the video file on local disk
#     video_file = request.files['video-blob']
#     video_file.save(os.path.join(app.config['UPLOAD_FOLDER'], key + '.webm'))
# 
#     # # Connect to the localhost database
#     # mydb = mysql.connector.connect(
#     #     host="localhost",
#     #     db="robotaxi",
#     #     user="root",
#     #     password="Mturk$35@"
#     # )
# 
#     # store the video file and other data on a database
#     #cursor = mydb.cursor()
#     #sql_insert_blob_query = """ INSERT INTO player (player_id, video) VALUES (%s, %s)"""
#     #insert_blob_tuple = (player_id, video_file)
#     #result = cursor.execute(sql_insert_blob_query, insert_blob_tuple)
#     #mydb.commit()
# 
#     # if the connection exists, end the connection
#     # if mydb.is_connected():
#     #     cursor.close()
#     #     mydb.close()
# 
#     return 'finished?'

@app.route('/sign_s3/')
def sign_s3():
    #   S3_BUCKET = os.environ.get('S3_BUCKET')
    S3_BUCKET = 'robotaxi'
    file_name = request.args.get('file_name')
    file_type = request.args.get('file_type')

    s3 = boto3.client('s3', region_name='us-east-2', config = boto3.session.Config(signature_version='s3v4'))

    presigned_post = s3.generate_presigned_post(
        Bucket = S3_BUCKET,
        Key = file_name,
        Fields = {"acl": "public-read", "Content-Type": file_type},
        Conditions = [
            {"acl": "public-read"},
            {"Content-Type": file_type}
        ],
        ExpiresIn = 3600
    )

    return json.dumps({
        'data': presigned_post,
        'url': 'https://%s.s3.amazonaws.com/%s' % (S3_BUCKET, file_name),
        'key': file_name
    })

def ran_gen(size, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

@app.route('/', methods=['GET', 'POST'])
def page():
    #with app.app_context():
    key = ran_gen(16, "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")
    session[key] = RoboTaxi()

    #Fire up the javascript page
    return render_template('robotaxi_game.html', key=key)
