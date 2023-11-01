from flask import Flask, render_template, redirect, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
from addition import login_required


app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    return render_template('logout.html')

@app.route('/register')
def register():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)