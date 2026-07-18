from flask import Blueprint, request, session, jsonify, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from databaseFunctions import addUser, getUser
from databaseTables import get_engine
from sqlalchemy.orm import Session

login_bp = Blueprint('login', __name__)

# @app.post('/chatbot/login-validation')
@login_bp.post('/chatbot/login-validation')
def validateLogin():
    """
    Using post request data (login credentials sent by client), checks to see if the user exists, then compares
    the hashed password for that user.

    If the user does not exist or the passwords do not match, the response status is 'error-invalid-login'

    If the user exists and the password matches, the user is logged in and the status is 'success'
    """

    data = request.get_json()

    username = data.get('username')
    password = data.get('password')


    with Session(get_engine()) as sesh:
        user = getUser(session=sesh, username=username, full_load=False)
        if user:
            # if the password matches, login the user
            if(check_password_hash(pwhash=user.password, password=password)):
                session['username'] = username
                response = jsonify({"status": "success"})
                response.set_cookie("login-status", 'true', samesite='Lax')
                return response, 200
            
        # # dummy hash check to ensure the program takes roughly the same amount of time to process an invalid username
        # # as an invalid password
        # else:
        #     dummy_hash = "scrypt:32768:8:1$dummy$d092d6b38c29b47e24446e1f0e42a9d6"
        #     check_password_hash(pwhash=dummy_hash, password='dummy-password')

        # if the user does not exist or the password does not match, send the following failed response
        response = jsonify({"status": 'error-invalid-login'})
        response.set_cookie("login-status", "false", samesite='Lax')
        return response, 400


# @app.route('/chatbot/logout')
@login_bp.route('/chatbot/logout')
def logoutUser():
    loginStatus = request.cookies.get('login-status')

    # response = jsonify({
    #     "status": "logout-failed",
    # })
    
    response = (redirect(url_for('chatbot.openChatBotPage')))

    if (loginStatus == 'true'):
        # response = jsonify({
        #     "status": "complete",
        # })
        # response.set_cookie('login-status', 'false')

        # clear login related cookies
        session.pop('username') # remove the login username
        response.delete_cookie('login-status') # remove the login-status cookie

        for cookie in request.cookies:
            response.delete_cookie(cookie)

        return response

    return response


@login_bp.post('/chatbot/create-account')
def createUserAccount():
    """
    Fetches the username and password and attempts to create an account.
    If the username already exists, this returns a status of 'error-user-exists'
    Otherwise, it returns a status of 'success'
    """

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    hashedPassword = generate_password_hash(password=password, method='scrypt')

    engine = get_engine()

    with Session(engine) as sesh: 
    # attempts to fetch user from database, if not found, user = None
    # full_load determines if all of the chats and files will be forced to load with the user (False=do not load everything)
        result, __ = addUser(session=sesh, username=username, password=hashedPassword) # result = false if failed
    # if user already exists, return user exists error
    if not result: # result = false if failed to add user
        response = jsonify({'status': 'error-user-exists'})
        response.set_cookie(key="login-status", value='false', samesite='Lax')
        return response, 400


    # if a user was successfully added, also login the user
    session['username'] = username
    response = jsonify({"status": "success"})
    response.set_cookie(key="login-status", value='true', samesite='Lax')

    return response, 200



# @app.route('/chatbot/login/')
@login_bp.route('/chatbot/login')
def openChatBotLoginPage():
    return render_template("chatbot-login-page.html")


@login_bp.route('/chatbot/register')
def openChatBotRegistrationPage():
    return render_template("chatbot-register-page.html")
