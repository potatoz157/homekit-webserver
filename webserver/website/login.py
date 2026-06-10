from flask import Blueprint, request, session, jsonify, redirect, url_for, render_template

login_bp = Blueprint('login', __name__)

# @app.post('/chatbot/login-validation')
@login_bp.post('/chatbot/login-validation')
def validateLogin():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    # for now, comparison is hard coded, later check against a database
    if (username == 'potatoz' and password == "123456"):

        # if the login is valid, set cookie value (set session username)
        session['username'] = username

        # alternatively, you can manually set the cookie instead of using sessions by doing:
        # response = jsonify({"status": "logged-in"})
        # response.set_cookie('username', username, httponly=True, samesite='Lax') # httponly for security
        # to access the raw cookie, inside of the post request function(s), use request.cookies.get('username')

        # after successful login, redirect back to chat page (redirect handled in javascript)

        # make a raw cookie (to access via js) that indicates login status:
        response = jsonify({"status": "logged-in"})
        response.set_cookie("login-status", 'true', samesite='Lax')
        
        return response, 200


        # return jsonify({
        #     "status": "logged-in"
        # }), 200
    
    response = jsonify({"status": "login-failed"})
    response.set_cookie("login-status", 'false', samesite='Lax')

    return response, 401


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

        return response

    return response


# @app.route('/chatbot/login/')
@login_bp.route('/chatbot/login/')
def openChatBotLoginPage():
    return render_template("chatbot-login-page.html")