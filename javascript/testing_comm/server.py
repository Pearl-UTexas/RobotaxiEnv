 # docs @ http://flask.pocoo.org/docs/1.0/quickstart/

from flask import Flask, jsonify, request, render_template
import requests as req
import subprocess
import mysql.connector
import os
import random

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'storage/'

@app.route('/RL', methods=['GET', 'POST'])
def learning():

    # POST request
    if request.method == 'POST':
        # to debug
        print('Incoming..')
        print(request.get_json())  # parse as JSON

        # Javascript has returned a json. parse through

        # Probably user input, video/audio raw data

        # RL/Pytorch

        # Process outputs back into correct states/actions (JSON)

        #return
        return 'OK', 200

    # GET request
    else:
        message = {'greeting':'Hello from Flask!'}
        return jsonify(message)  # serialize and use JSON headers

@app.route('/finish', methods=['POST'])
def finish():
    print('finish method on python server')
    # Store the video file recieved
    if request.method == 'POST':

        mydb = mysql.connector.connect(
            host="localhost",
            db="robotaxi",
            user="root",
            password="Mturk$35@"
        )

        print('Connected to database')

        cursor = mydb.cursor()
        sql_insert_blob_query = """ INSERT INTO player (player_id, video) VALUES (%s, %s)"""

        player_id = random.randint(10000, 99999)
        video_file = request.files['video-blob']
        print(os.path.join(app.config['UPLOAD_FOLDER'], 'test.webm'))
        video_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'test.webm'))
        print('Got video file!')
        
        #insert_blob_tuple = (player_id, video_file)
        #result = cursor.execute(sql_insert_blob_query, insert_blob_tuple)
        #mydb.commit()
        #print("Image and file inserted successfully as a BLOB into player")

        if mydb.is_connected():
            cursor.close()
            mydb.close()
            print("Connection to database closed")
        
        return 'finished?'
    else:
        return "ERROR: Only POST requests allowed for /finish"

    
@app.route('/', methods=['GET', 'POST'])
def page():

    #Fire up the javascript page
    return render_template('index.html')
