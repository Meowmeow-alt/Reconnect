import sqlite3
from flask import Flask, render_template, redirect, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
from addition import login_required

db = sqlite3.connect("user.db")

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)


@app.route('/', methods=['GET','POST'])
def index():
    return render_template("index.html")


@app.route('/login', methods=['GET','POST'])
def login():
    session.clear()
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return "must provide username", 403
        if not password:
            return "must provide password", 403
        
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return "invalid username and/or password", 403

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        return redirect('/')

    return render_template('login.html')


@app.route('/logout', methods=['GET','POST'])
@login_required
def logout():
    return render_template('logout.html')


@app.route('/register', methods=['GET','POST'])
def register():
    return render_template('register.html')


if __name__ == '__main__':
    app.run(debug=True)


