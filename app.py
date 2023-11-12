from cs50 import SQL
from flask import Flask, render_template, redirect, request, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
from flask_session import Session
import json
from addition import login_required


app = Flask(__name__)
app.config['SECRET_KEY'] = 'for something secretive'
app.config['IMG_FOLDER'] = 'static/img/images'
app.config['PROFILE_FOLDER'] = 'static/img/profile'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///reconnect.db")


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


"""
# ROUTE FOR BASE FEATURES
"""
@app.route('/', methods=['GET','POST'])
def index():
    return render_template("index.html")


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("must provide username/password")
            return redirect(request.url)

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], password):
            flash("invalid username and/or password")
            return redirect(request.url)

        if rows[0]['person_details_id'] is None:
            return redirect('/personal')

        session["username"] = username
        session['personal_details_id'] = rows[0]['person_details_id']
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
            flash("must provide username/password")
            return redirect(request.url)
        if password != confirm or not confirm:
            flash("Password and confirmation do not match!")
            return redirect(request.url)
        usernames = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(usernames) > 0:
            flash("Username already exists, choose another one")
            return redirect(request.url)

        hashpass = generate_password_hash(password)
        db.execute("INSERT INTO users (username, password) VALUES (?,?)", username, hashpass)

        session["username"] = username
        return redirect('/personal')

    return render_template('register.html')


@app.route('/personal', methods=['GET', 'POST'])
def personal():
    if request.method == 'POST':
        name = request.form.get('name').title()

        age = int(request.form.get('age'))
        if age not in range(1,180):
            flash('Age Invalid')
            return redirect(request.url)

        city = int(request.form.get('city'))

        sex = request.form.get('sex')
        sex = 0 if sex == 'Female' else 1

        height = int(request.form.get('height'))

        marks = request.form.get('marks')

        phone = request.form.get('phone')
        if phone.isdigit() == False or len(phone) > 12 or len(phone) < 10:
            flash('Invalid phone number')
            return redirect(request.url)

        mail = request.form.get('mail').lower()
        if '@' not in mail and '.' not in mail:
            flash('Invalid email address')
            return redirect(request.url)

        db.execute("INSERT INTO person_details (username, name, age, city, biological_sex, height, distinguishing_marks, phone, mail)\
            VALUES (?,?,?,?,?,?,?,?,?)", session["username"], name, age, city, sex, height, marks, phone, mail)

        rows = db.execute("SELECT id FROM person_details WHERE username = ?", session["username"])
        person_details_id = rows[0]['id']
        db.execute("UPDATE users SET person_details_id = ? WHERE username = ?", person_details_id, session["username"])

        session['personal_details_id'] = person_details_id
        return redirect('/')

    with open('json/location.json', 'r') as f:
            location = json.load(f)
    with open('json/height.json', 'r') as f:
            height = json.load(f)
    return render_template('personal.html', location=location, height=height)


"""
# ROUTE FOR MAIN FEATURES
"""
@app.route('/search', methods=['GET','POST'])
@login_required
def search():
    return render_template('search.html')


@app.route('/upload', methods=['GET','POST'])
@login_required
def upload():
    return render_template('upload.html')


@app.route('/result', methods=['GET','POST'])
@login_required
def result():
    return render_template('result.html')


@app.route('/contact', methods=['GET','POST'])
@login_required
def contact():
    return render_template('contact.html')


"""
# ROUTE FOR SIDE PAGE ON NAVBAR
"""
@app.route('/portfolio', methods=['GET','POST'])
@login_required
def portfolio():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['PROFILE_FOLDER'], filename))
            db.execute('INSERT INTO images (photo_path) VALUES (?)', os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img_id = db.execute('SELECT last_insert_rowid()')[0]['last_insert_rowid()']
            db.execute('UPDATE person_details SET img_id = ? WHERE username = ?', img_id, session['username'])

    return render_template('portfolio.html')


"""
# ERROR HANDLERS
"""
@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.errorhandler(400)
def bad_request(e):
    return render_template('400.html'), 400


if __name__ == '__main__':
    app.run(debug=True)


