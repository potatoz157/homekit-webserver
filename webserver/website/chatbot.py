from flask import Blueprint, request, session, jsonify, redirect, url_for, render_template, make_response
from databaseFunctions import getUser
from databaseTables import get_engine
from sqlalchemy.orm import Session
from uuid import uuid4
from globals import getActiveUsers
import time

# all URLS inside of chat_bp will automatically have their route start with /chatbot/ because of the 3rd argument
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')

# @app.route('/chatbot/')
@chatbot_bp.route('/')
def openChatBotPage():
    # check for valid login if username is in the session (validity check needed if the database was updated but the user is still logged in)
    # for example if a user account was deleted but the account is still logged in, perform a check for username existence
    response = make_response(render_template("ai-assistant.html"))

    if 'username' in session:
        username = session.get('username')
        if username:
            with Session(get_engine()) as sesh:
                user_exists = getUser(session=sesh, username=username, full_load=False)
                if not user_exists:
                    session.pop('username')
                    response.set_cookie(key='login-status', value='false', samesite='Lax')

    else:
        response.set_cookie(key='login-status', value='false', samesite='Lax')

    # if the user does not already have an ID, give the user an ID
    if 'user-id' not in session:
        uuid = generateUserId()
        session['user-id'] = uuid # give every user an ID (both guests and logged in users)

        # add the new user UUID to the global dictionary (variable in apiCalls.py) and initialze the value for the UUID key (value of json object key)
        active_users = getActiveUsers()
        active_users[uuid] = {
            'interruptChat': False,
            'last-seen': time.time()
        }
    else:
        user_id = session['user-id'] # give every user an ID (both guests and logged in users)

        # add the new user UUID to the global dictionary (variable in apiCalls.py) and initialze the value for the UUID key (value of json object key)
        active_users = getActiveUsers()
        active_users[user_id] = {
            'interruptChat': False,
            'last-seen': time.time()
        }
    return response



# define helper function:
# the guest ID is used to keep track of each user's running/streaming chats (both guest and logged in users)
def generateUserId() -> str:

    # generate a unique ID string for the given user
    UUID = str(uuid4()) # using builtin library for UUID, generate an ID. Has extremely low chance of duplicating an existing ID

    # Later, save these ID's in a temporary database and check for existing ID's. If an existing ID is found, make a new ID and check if it exists again for 100% certainty.

    return UUID