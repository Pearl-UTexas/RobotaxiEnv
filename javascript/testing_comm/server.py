 # docs @ http://flask.pocoo.org/docs/1.0/quickstart/

from flask import Flask, jsonify, request, render_template
import requests as req

app = Flask(__name__)

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
    # Get and store the video file recieved
    if request.method == 'POST':
        print('url')
        print(request.get_data())
        
        return 'finished?'
    else:
        return "ERROR: Only POST requests allowed for /finish"
            

@app.route('/', methods=['GET', 'POST'])
def page():

    #Fire up the javascript page
    return render_template('index.html')
