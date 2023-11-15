from cs50 import SQL
from flask import Flask, render_template, request
from werkzeug.security import check_password_hash, generate_password_hash
import os
from flask_session import Session
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = 'for something secretive'
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
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    rows = db.execute("SELECT * FROM users WHERE username = ?", username)
    if len(rows) != 1 or not check_password_hash(rows[0]["password"], password):
        return "Invalid username and/or password", 403
    return {'rows':rows[0]}



@app.route('/register', methods=['GET','POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    usernames = db.execute("SELECT * FROM users WHERE username = ?", username)
    if len(usernames) > 0:
        return "Username already exists, choose another one", 403

    hashpass = generate_password_hash(password)
    db.execute("INSERT INTO users (username, password) VALUES (?,?)", username, hashpass)



@app.route('/personal', methods=['GET', 'POST'])
def personal():
    data = request.get_json()
    username = data.get('username')
    name = data.get('name')
    age = data.get('age')
    city = data.get('city')
    sex = data.get('sex')
    height = data.get('height')
    marks = data.get('marks')
    phone = data.get('phone')
    mail = data.get('mail')

    person = db.execute("SELECT id FROM person_details WHERE username = ?", username)

    if person:
        person_details_id = rows[0]['id']
        db.execute("UPDATE person_details SET name = ?, age = ?, city = ?, biological_sex = ?, height = ?, distinguishing_marks = ?, phone = ?, mail = ? WHERE id = ?",
                   name, age, city, sex, height, marks, phone, mail, person_details_id)
    else:
        db.execute("INSERT INTO person_details (username, name, age, city, biological_sex, height, distinguishing_marks, phone, mail)\
            VALUES (?,?,?,?,?,?,?,?,?)", username, name, age, city, sex, height, marks, phone, mail)
        rows = db.execute("SELECT id FROM person_details WHERE username = ?", username)
        person_details_id = rows[0]['id']

    db.execute("UPDATE users SET person_details_id = ? WHERE username = ?", person_details_id, username)

    return {'person_details_id':person_details_id}



"""
# ROUTE FOR MAIN FEATURES
"""



"""
# ROUTE FOR SIDE PAGE ON NAVBAR
"""
@app.route('/portfolio', methods=['GET', 'POST'])
def portfolio():
    data = request.get_json()
    person_details_id = data.get('person_details_id')

    if request.method == 'POST':
        photo_path = data.get('photo_path')

        profile = db.execute('SELECT photo_path FROM images\
                              JOIN person_details ON images.id = person_details.img_id\
                              WHERE person_details.id = ?', person_details_id)
        
        if not profile: # path hasn't existed, create new photo_path and update img_id in person_details table
            db.execute("INSERT INTO images (photo_path, relationship) VALUES (?, 'profile')", photo_path)
            
            img_id = db.execute("SELECT last_insert_rowid() AS id")[0]["id"]
            db.execute("UPDATE person_details SET img_id = ? WHERE id = ?", img_id, person_details_id)

        if profile: # path has already existed, update old_path with a new one.
            old_path = profile[0]['photo_path']
            old_path = os.path.join('../frontend', old_path)

            if os.path.isfile(old_path):
                os.remove(old_path)
                
            img_id = db.execute("SELECT img_id FROM person_details WHERE id = ?", person_details_id)[0]['img_id']
            db.execute("UPDATE images SET photo_path = ? WHERE id = ?", photo_path, img_id)

        return {'person_details_id':person_details_id}

    else:
        photo_path = db.execute('SELECT photo_path\
                                  FROM images\
                                  JOIN person_details ON images.id = person_details.img_id\
                                  WHERE person_details.id = ?', person_details_id)
        
        person_details = db.execute("SELECT * FROM person_details WHERE id = ?", person_details_id)
        
        photo_path = photo_path[0]['photo_path'] if photo_path else None

        return {'photo_path': photo_path, 'details': person_details[0]}



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
    app.run(debug=True, port=5001)

