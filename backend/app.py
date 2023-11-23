from cs50 import SQL
from flask import Flask, request, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import os
from flask_session import Session
import uuid
import numpy as np
import pickle
import cv2
from insightface.app import FaceAnalysis


app = Flask(__name__)
app.config['SECRET_KEY'] = 'for something secretive'
app.config['IMG_FOLDER'] = 'img/images'
app.config['PROFILE_FOLDER'] = 'img/profile'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

face_analysis = FaceAnalysis(name="buffalo_l", allowed_modules=["detection", "recognition"])
face_analysis.prepare(ctx_id=0, det_size=(640, 640))

db = SQL("sqlite:///reconnect.db")


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route('/get_image', methods=['GET'])
def get_image():
    photo_path = request.args.get('photo_path')
    return send_file(photo_path, mimetype='image/jpeg')


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
    return "Successfully registered", 200


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

    rows = db.execute("SELECT id FROM person_details WHERE username = ?", username)

    if rows:
        person_details_id = rows[0]['id']
        db.execute("UPDATE person_details SET name = ?, age = ?, city = ?, biological_sex = ?, height = ?, distinguishing_marks = ?, phone = ?, mail = ? WHERE id = ?",
                   name, age, city, sex, height, marks, phone, mail, person_details_id)
    else:
        db.execute("INSERT INTO person_details (username, name, age, city, biological_sex, height, distinguishing_marks, phone, mail)\
            VALUES (?,?,?,?,?,?,?,?,?)", username, name, age, city, sex, height, marks, phone, mail)
        person_details_id = db.execute("SELECT last_insert_rowid() AS id")[0]["id"]

    db.execute("UPDATE users SET person_details_id = ? WHERE username = ?", person_details_id, username)

    return {'person_details_id':person_details_id}



"""
# ROUTE FOR MAIN FEATURES
"""
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        img = request.files['img']
        filename = secure_filename(img.filename)
        filename = str(uuid.uuid4()) + "_" + filename
        photo_path = os.path.join(app.config['IMG_FOLDER'], filename)
        
        relate = request.form.get('relate')
        username = request.form.get('username')
        name = request.form.get('name')
        age = request.form.get('age')
        city = request.form.get('city')
        sex = request.form.get('sex')
        height = request.form.get('height')
        marks = request.form.get('marks')
        phone = request.form.get('phone')
        mail = request.form.get('mail')
        last_seen = request.form.get('last_seen')

        rows = db.execute('SELECT * FROM person_details WHERE username = ?', username)
        if rows:
            row = rows[0]
            if row['name'] == name and row['age'] == age and row['city'] == city and row['biological_sex'] == sex and\
            row['height'] == height and row['last_seen_year'] == last_seen:
                return "This profile already exists", 403
        
        db.execute("INSERT INTO images (photo_path, relationship) VALUES (?,?)", photo_path, relate)
 
        img_id = db.execute("SELECT last_insert_rowid() AS id")[0]["id"]
        db.execute("INSERT INTO person_details (username, name, age, city, biological_sex, height, distinguishing_marks, phone, mail, last_seen_year, img_id)\
            VALUES (?,?,?,?,?,?,?,?,?,?,?)", username, name, age, city, sex, height, marks, phone, mail, last_seen, img_id)

        img.save(photo_path)
        return "Successfully", 200

    else:
        data = request.get_json()
        username = data.get('username')

        people = db.execute(""" SELECT p.*, i.photo_path
                                FROM person_details p
                                JOIN images i ON p.img_id = i.id
                                WHERE p.username = ? AND i.relationship != 'profile'
                            """, username)
        people.reverse()
        return {'people':people}



@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':
        data = request.get_json()
        id = data.get('id')
        photo_path = data.get('photo_path')

        if photo_path:
            photo_path = os.path.join('../frontend', photo_path)
            if os.path.isfile(photo_path):
                try:
                    os.remove(photo_path)
                except Exception as e:
                    print("Error deleting file: ", e)
                    return "Failed to delete file", 500

        db.execute("UPDATE person_details SET status = TRUE WHERE id = ?", id)

    return "Successfully delete", 200



"""
# ROUTE FOR SIDE PAGE ON NAVBAR
"""
@app.route('/portfolio', methods=['GET', 'POST'])
def portfolio():
    if request.method == 'POST':
        person_details_id = request.form.get('person_details_id')
        img = request.files['img']
        filename = secure_filename(img.filename)
        filename = str(uuid.uuid4()) + "_" + filename
        photo_path = os.path.join(app.config['PROFILE_FOLDER'], filename)
        img.save(photo_path)

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
        data = request.get_json()
        person_details_id = data.get('person_details_id')
        photo_path = db.execute('SELECT photo_path\
                                  FROM images\
                                  JOIN person_details ON images.id = person_details.img_id\
                                  WHERE person_details.id = ?', person_details_id)
        
        person_details = db.execute("SELECT * FROM person_details WHERE id = ?", person_details_id)
        
        photo_path = photo_path[0]['photo_path'] if photo_path else None

        return {'photo_path': photo_path, 'details': person_details[0]}


if __name__ == '__main__':
    app.run(debug=True, port=5001)

