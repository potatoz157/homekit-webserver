from flask import Flask, render_template, request, jsonify, Response, session, redirect, url_for, make_response
from helperFunctions import openOllama

from login import login_bp
from apiCalls import api_bp
from chatbot import chatbot_bp


app = Flask(
    __name__, 
    # template_folder="website/actualUI", # only use this if the folder for the .html is not templates/
    # static_folder="website/actualUI", # only use this if the folder for the css and js are not static/css and static/js
    # static_url_path=''
)

# register the routes (i.e. app.route, app.get, etc. from other define python scripts
app.register_blueprint(login_bp) 
app.register_blueprint(api_bp)
app.register_blueprint(chatbot_bp)

app.secret_key = 'super-duper-secret-key' # change later

def init():
    openOllama()

@app.route('/')
def openHome():
    return render_template("homepage.html")
    # return render_template("AI_Assistant.html")


@app.route('/security-cameras/')
def openSecurityCameraPage():
    return render_template("security-camera.html")

# @app.route('/security-camera/video-feed-pipeline')
# def videoFeed():
#     global cap
#     return Response(generateFrames(cap), mimetype='multipart/x-mixed-replace; boundary=frame')



if __name__ == '__main__':
    index = 0
    init()
    # cap = openCamera(index)
    print("\n\nTo connect (via wifi) use Wifi IPv4 (default): 192.168.1.167:5000\n")
    app.run(debug=False, host="0.0.0.0", port=5000)