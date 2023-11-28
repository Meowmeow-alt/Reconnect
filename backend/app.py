from cs50 import SQL
from flask import Flask, request, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import os
from flask_session import Session
import uuid
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import cv2
from insightface.app import FaceAnalysis
from addition import get_embed, read


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
    if photo_path.split('/')[-1] == 'None':
        return "This profile has been deleted", 403
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
@app.route('/search', methods=['POST'])
def search_post():
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
        row['height'] == height and row['last_seen_year'] == last_seen and row['status'] == False:
            return "This profile already exists", 403
    
    db.execute("INSERT INTO images (photo_path, relationship) VALUES (?,?)", photo_path, relate)

    img_id = db.execute("SELECT last_insert_rowid() AS id")[0]["id"]
    person_details_id = db.execute("INSERT INTO person_details (username, name, age, city, biological_sex, height, distinguishing_marks, phone, mail, last_seen_year, img_id)\
        VALUES (?,?,?,?,?,?,?,?,?,?,?)", username, name, age, city, sex, height, marks, phone, mail, last_seen, img_id)

    img.save(photo_path)

    # define pickle file and numpy file
    try:
        mapping = pickle.load(open('uploads.pkl', 'rb'))
    except:
        mapping = []
    
    try:
        old_embeds = np.load('uploads.npy')
    except:
        old_embeds = np.array([])
    
    # get embed from the image
    photo_path = os.path.join('../backend', photo_path)
    img = read(photo_path)
    embed = get_embed(img)

    # numpy embeds
    if old_embeds.size > 0:
        updated_embeds = np.vstack((old_embeds, embed)) if not any(np.array_equal(embed, old) for old in old_embeds) else None
    else:
        updated_embeds = embed.reshape(1,-1)

    if updated_embeds is not None:
        np.save('uploads.npy', updated_embeds)

    # pickle mapping
    if not any(np.array_equal(embed, old) for old in old_embeds):
        mapping.append(person_details_id)
    else:
        return "Fail to map", 403

    with open('uploads.pkl', 'wb') as f:
        pickle.dump(mapping, f)

    return "Successfully", 200


@app.route('/search', methods=['GET'])
def search_get():
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
        photo_path = data.get('photo_path').split('=')[1]

        if photo_path:
            photo_path = os.path.join('../backend', photo_path)
            if os.path.isfile(photo_path):
                try:
                    os.remove(photo_path)
                except Exception as e:
                    return "Failed to delete file", 500

        db.execute("UPDATE person_details SET status = TRUE WHERE id = ?", id)
        db.execute("""UPDATE images
                      SET photo_path = 'None'
                      WHERE id IN (
                      SELECT img_id 
                      FROM person_details 
                      WHERE id = ?
                    );""", id)

    return "Successfully delete", 200


@app.route('/result', methods=['GET'])
def result():
    """
    Prepare files and datas
    """
    other_embeds = np.load('uploads.npy')
    user_embeds = np.load('users.npy')
    with open('uploads.pkl', 'rb') as f:
        other_ids = pickle.load(f)
    with open('users.pkl', 'rb') as f:
        user_ids = pickle.load(f)

    data = request.get_json()
    username = data['username']

    people = db.execute("SELECT * FROM person_details WHERE username = ?", username)
    status = [person['status'] for person in people]

    ids = [person['id'] for person in people if person['status'] == 0]
    filtered_ids = []
    for id in ids:
        find_me = db.execute("SELECT find_me FROM users WHERE person_details_id = ?", id)
        if all(find['find_me'] != 0 for find in find_me):
            filtered_ids.append(id) 
    ids = filtered_ids
    
    """
    Cosine similarity section
    """
    similarity_matrix = cosine_similarity(user_embeds, other_embeds)

    threshold = 0.56
    pairs = []
    for i in range(similarity_matrix.shape[0]):
        for j in range(similarity_matrix.shape[1]):
            number = similarity_matrix[i, j]
            if number > threshold:
                user_id = user_ids[i]
                other_id = other_ids[j]
                pairs.append((user_id, other_id))

    uu = [db.execute("""SELECT p.id, i.photo_path FROM images i
                          JOIN person_details p ON p.img_id = i.id
                          WHERE p.id = ?""", id)[0] for id, _ in pairs]
    pp = [db.execute("""SELECT p.id, i.photo_path FROM images i
                          JOIN person_details p ON p.img_id = i.id
                          WHERE p.id = ?""", id)[0] for _, id in pairs]

    pairs = [(u['id'], p['id']) for u, p in zip(uu, pp) if u['photo_path'] != 'None' and p['photo_path'] != 'None']

    for user_id, other_id in pairs:
        try:
            existing_match = db.execute("SELECT * FROM matches WHERE person_details_id1 = ? AND person_details_id2 = ?", user_id, other_id)[0]['match_score']
        except:
            existing_match = None
        score = round(float(number),4)

        if not existing_match:
            img1_id = db.execute("SELECT img_id FROM person_details WHERE id = ?", user_id)[0]['img_id']
            img2_id = db.execute("SELECT img_id FROM person_details WHERE id = ?", other_id)[0]['img_id']

            db.execute("INSERT INTO matches (img1_id, img2_id, person_details_id1, person_details_id2, status, match_score) VALUES (?, ?, ?, ?, 'onsite', ?)",
                        img1_id, img2_id, user_id, other_id, score)
            
        if existing_match != score:
            db.execute("UPDATE matches SET match_score = ? WHERE person_details_id1 = ? AND person_details_id2 = ?", score, user_id, other_id)

    check = [None if id[0] not in ids and id[1] not in ids else 1 for id in pairs]
    
    if not check:
        return "No match at the moment", 403

    if not any(s == 0 for s in status):
        return "No match at the moment.", 403
    
    print("Hellooooooooooooo pairs", pairs)
    
    """
    Matching result section
    """
    user = []
    pair = []
    existed_ids = []

    for session_id, pair_id in pairs:
        if session_id in ids or pair_id in ids:
            print("Hellooooooooooooo session_id", session_id)
            print("Hellooooooooooooo pair_id", pair_id)
            if session_id not in existed_ids and pair_id not in existed_ids:
                user_details = db.execute("""SELECT p.*, i.photo_path
                                            FROM person_details p
                                            JOIN images i ON p.img_id = i.id
                                            WHERE p.id = ?
                                        """, session_id)
                pair_details = db.execute("""SELECT p.*, i.photo_path
                                            FROM person_details p
                                            JOIN images i ON p.img_id = i.id
                                            WHERE p.id = ?
                                        """, pair_id)
                user.append(user_details[0])
                pair.append(pair_details[0])
                existed_ids.append(session_id)
                existed_ids.append(pair_id)

    return {'user':user, 'pair':pair}


# @app.route('/decline', methods=['GET'])
# def decline():
#     f
    

"""
# ROUTE FOR SIDE PAGE ON NAVBAR
"""
@app.route('/portfolio', methods=['POST'])
def portfolio_post():
    person_details_id = request.form.get('person_details_id')
    img = request.files['img']
    filename = secure_filename(img.filename)
    filename = str(uuid.uuid4()) + "_" + filename
    photo_path = os.path.join(app.config['PROFILE_FOLDER'], filename)

    profile = db.execute('SELECT photo_path FROM images\
                            JOIN person_details ON images.id = person_details.img_id\
                            WHERE person_details.id = ?', person_details_id)
    
    if not profile: # path hasn't existed, create new photo_path and update img_id in person_details table
        db.execute("INSERT INTO images (photo_path, relationship) VALUES (?, 'profile')", photo_path)
        
        img_id = db.execute("SELECT last_insert_rowid() AS id")[0]["id"]
        db.execute("UPDATE person_details SET img_id = ? WHERE id = ?", img_id, person_details_id)

    if profile: # path has already existed, update old_path with a new one.
        old_path = profile[0]['photo_path']
        old_path = os.path.join('../backend', old_path)

        if os.path.isfile(old_path):
            os.remove(old_path)
            
        img_id = db.execute("SELECT img_id FROM person_details WHERE id = ?", person_details_id)[0]['img_id']
        db.execute("UPDATE images SET photo_path = ? WHERE id = ?", photo_path, img_id)
    
    img.save(photo_path)

    # define pickle file and numpy file
    try:
        mapping = pickle.load(open('users.pkl', 'rb'))
    except:
        mapping = []
    
    try:
        old_embeds = np.load('users.npy')
    except:
        old_embeds = np.array([])
    
    # get embed from the image
    photo_path = os.path.join('../backend', photo_path)
    img = read(photo_path)
    embed = get_embed(img)

    # numpy embeds
    if old_embeds.size == 0:
        updated_embeds = embed.reshape(1,-1)
    else:
        updated_embeds = np.vstack((old_embeds, embed)) if not any(np.array_equal(embed, old) for old in old_embeds) else None
    if updated_embeds is not None:
        np.save('users.npy', updated_embeds)

    # pickle mapping
    if not any(np.array_equal(embed, old) for old in old_embeds):
        mapping.append(int(person_details_id))

    with open('users.pkl', 'wb') as f:
        pickle.dump(mapping, f)

    return {'person_details_id':person_details_id}


@app.route('/portfolio', methods=['GET'])
def portfolio_get():
    data = request.get_json()
    person_details_id = data.get('person_details_id')
    username = data.get('username')

    photo_path = db.execute(""" SELECT photo_path
                                FROM images
                                JOIN person_details ON images.id = person_details.img_id
                                WHERE person_details.id = ?""", person_details_id)
    
    person_details = db.execute(""" SELECT p.*, u.find_me
                                    FROM person_details p
                                    JOIN users u ON u.person_details_id = ?
                                    WHERE id = ?""", person_details_id, person_details_id)
    
    photo_path = photo_path[0]['photo_path'] if photo_path else None

    history = db.execute("""SELECT * FROM matches m
                            JOIN person_details p ON p.id = m.person_details_id1 
                            OR p.id = m.person_details_id2
                            WHERE username = ?""", username)

    return {'photo_path': photo_path, 'details': person_details[0], 'history':history}


@app.route('/findme', methods=['GET','POST'])
def findme():
    data = request.get_json()
    person_details_id = data.get('person_details_id')

    img_id = db.execute("SELECT img_id FROM person_details WHERE id = ?", person_details_id)[0]['img_id']
    
    if img_id:
        db.execute("UPDATE users SET find_me = TRUE WHERE person_details_id = ?", person_details_id)
        return "Successfully loaded", 200
    else:
        return "Please upload your profile photo first.", 403


@app.route('/disable_findme', methods=['POST'])
def disable_findme():
    data = request.get_json()
    username = data.get('username')
    db.execute("UPDATE users SET find_me = FALSE WHERE username = ?", username)
    return "Successfully loaded", 200


if __name__ == '__main__':
    app.run(debug=True, port=5001)

