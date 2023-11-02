from cs50 import SQL
from flask import Flask, render_template, redirect, request, session, flash, g
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
from addition import login_required


app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)

db = SQL("sqlite:///user.db")


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route('/', methods=['GET','POST'])
def index():
    return render_template("index.html")


@app.route('/login', methods=['GET','POST'])
def login():
    session.clear()

    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return "must provide username/password", 403
        
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], password):
            return "invalid username and/or password", 403

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        return redirect('/')

    return render_template('login.html')


@app.route('/logout', methods=['GET','POST'])
@login_required
def logout():
    session.clear()
    return redirect("/")


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")

        if not username or not password:
            return "must provide username/password", 400
        if password != confirm or not confirm:
            flash("Password and confirmation do not match!")
        usernames = [row['username'] for row in db.execute("SELECT * FROM users")]
        if username == usernames:
            flash("Username already exists")
        
        hashpass = generate_password_hash(password)
        db.execute("INSERT INTO users (username, password) VALUES (?,?)", username, hashpass)
        return redirect('/')
    
    return render_template('register.html')


if __name__ == '__main__':
    app.run(debug=True)


