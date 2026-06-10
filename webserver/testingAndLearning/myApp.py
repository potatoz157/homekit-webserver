from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
# The secret key is required by Flask to encrypt session data cookies securely
app.secret_key = "replace_this_with_a_long_secure_random_string"

@app.route('/')
def home():
    # If a user is logged in, show their dashboard. Otherwise, send them to login.
    if 'username' in session:
        return f"Hello, {session['username']}! You are logged in. <a href='/logout'>Logout</a>"
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        
        if username:
            # Create the session state using the username as the unique ID for now
            session['username'] = username
            return redirect(url_for('home'))
            
    return render_template('page.html')

@app.route('/logout')
def logout():
    # Clear the session data to completely log the user out
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)