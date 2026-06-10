from flask import Blueprint, request, session, jsonify, redirect, url_for, render_template

# all URLS inside of chat_bp will automatically have their route start with /chatbot/ because of the 3rd argument
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')

# @app.route('/chatbot/')
@chatbot_bp.route('/')
def openChatBotPage():
    return render_template("ai-assistant.html")