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
import ast
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
    person_details_id = db.execute("""INSERT INTO person_details 
        (status, username, name, age, city, biological_sex, height, distinguishing_marks, phone, mail, last_seen_year, img_id)
        VALUES (0,?,?,?,?,?,?,?,?,?,?,?)""", username, name, age, city, sex, height, marks, phone, mail, last_seen, img_id)

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
        updated_embeds = np.vstack((old_embeds, embed))
    else:
        updated_embeds = embed.reshape(1,-1)

    if updated_embeds is not None:
        np.save('uploads.npy', updated_embeds)

    # pickle mapping
    mapping.append(person_details_id)

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
    data = request.get_json()
    id = data.get('id')
    username = data.get('username')

    try:
        upload_embeds = np.load('uploads.npy') # embed của toàn bộ ảnh upload
        user_embeds = np.load('users.npy') # embed của toàn bộ ảnh user 
        with open('uploads.pkl', 'rb') as f:
            pair_mapping_ids = pickle.load(f)
        with open('users.pkl', 'rb') as f:
            user_mapping_ids = pickle.load(f)
    except:
        return "Data have not existed", 403

    # lấy id của cùng username ngoại trừ session[‘id’] và có status = 0
    pair_ids = db.execute("""SELECT id FROM person_details 
                            WHERE username = ? AND status = 0 AND NOT id = ?""", 
                            username, id)
    pair_ids = [row['id'] for row in pair_ids]

    # lấy index của những id trong pair_ids từ file pickle sau đó lấy embed trong file numpy
    pair_indices = [pair_mapping_ids.index(pair_id) for pair_id in pair_ids]
    pair_embeds = upload_embeds[pair_indices]

    if pair_embeds.size < 1:
        return "No pair upload to match", 403
        
    # User_embed filter ra những người đã bật find_me
    user_ids = db.execute("SELECT person_details_id FROM users WHERE find_me = 1 AND NOT person_details_id = ?", id)
    user_ids = [item['person_details_id'] for item in user_ids]
    user_indices = [user_mapping_ids.index(user_id) for user_id in user_ids]
    valid_user_embeds = user_embeds[user_indices]

    # Cosine giữa pair_embeds với valid_user_embeds
    matrix = cosine_similarity(pair_embeds, valid_user_embeds)
    # Được một cái matrix - dòng là pair_embeds còn cột là valid_user_embeds

    # Được những cặp ids cosine với nhau
    threshold = 0.62
    valid_pair_user_ids = []
    for i in range(len(pair_ids)):
        for j in range(len(user_ids)):
            # so sánh với threshold
            if matrix[i][j] >= threshold:
                valid_pair_user_ids.append((pair_ids[i], user_ids[j]))
    valid_pair_user_ids = np.array(valid_pair_user_ids)

    # tìm value của user giống pair nhất
    user_match_pair_ids = np.argmax(matrix, axis=1)
    user_match_pair = matrix[np.arange(matrix.shape[0]), user_match_pair_ids]
    thr_filter = user_match_pair > threshold

    # tìm match_score
    match_score = user_match_pair[thr_filter].tolist()

    pairs_img_ids = []
    query = "SELECT img_id FROM person_details WHERE id IN (?)"
    for pairs in valid_pair_user_ids:
        pairs = tuple(map(str,pairs))
        img_ids = [row['img_id'] for row in db.execute(query, pairs)]
        pairs_img_ids.append(tuple(img_ids))

    # insert vào database
    for i in range(len(valid_pair_user_ids)):
        ids = valid_pair_user_ids.tolist()
        check_matches = db.execute("""SELECT pair_details_id, user_details_id FROM matches 
                                    WHERE pair_details_id = ? AND user_details_id = ?""",
                                    ids[i][0], ids[i][1])

        if not check_matches:
            db.execute("""INSERT INTO matches 
                    (img1_id,img2_id,pair_details_id,user_details_id,
                    pair_accept_status,match_score) VALUES (?,?,?,?,0,?)""", 
                    pairs_img_ids[i][0], pairs_img_ids[i][1], ids[i][0], ids[i][1], match_score[i])

    pairs_photo_paths = []
    query = "SELECT photo_path FROM images WHERE id IN (?)"
    for pairs in pairs_img_ids:
        # pairs = tuple(map(str,pairs))
        photo_paths = [row['photo_path'] for row in db.execute(query, pairs)]
        pairs_photo_paths.append(tuple(photo_paths))
    
    data = "SELECT name,age FROM person_details WHERE id IN (?)"
    try:
        temp = tuple(map(str,valid_pair_user_ids[:,0]))
    except:
        return "No match result at the moment", 403
    pair_data = db.execute(data, temp)

    match_score_list = [round(score,2) for score in match_score]

    status = []
    infos = []
    query = """SELECT pair_accept_status FROM matches 
                WHERE pair_details_id = ? AND user_details_id = ?"""
    for pairs in valid_pair_user_ids.tolist():
        status_pairs = db.execute(query, pairs[0], pairs[1])[0]['pair_accept_status']
        # một trong hai bên decline
        if int(status_pairs) == 1:
            status.append(1)
        # pair accept - gửi match result cho bên user
        elif int(status_pairs) == 2:
            status.append(2)
            info = db.execute("SELECT * FROM person_details WHERE id = ?", pairs[1])[0]
            infos.append(info)
        # trạng thái ban đầu
        else:
            status.append(0)

    return {'photo_paths':pairs_photo_paths, 'data':pair_data, 'match_score':match_score_list, 
            'pairs':valid_pair_user_ids.tolist(), 'status':status, 'infos':infos}


@app.route('/decline', methods=['GET', 'POST'])
def decline():
    data = request.get_json()
    pairs = ast.literal_eval(data.get('pairs'))
    username = data.get('username')
    id = data.get('id')

    pair_ids = db.execute("""SELECT id FROM person_details 
                            WHERE username = ? AND status = 0 AND NOT id = ?""", 
                            username, id)
    pair_ids = [row['id'] for row in pair_ids]

    # pair decline - không gửi cho user luôn
    db.execute("""UPDATE matches SET pair_accept_status = 1
                  WHERE pair_details_id = ? AND user_details_id = ?""",
                  pairs[0], pairs[1])

    return "Success", 200


@app.route('/accept', methods=['GET','POST'])
def accept():
    data = request.get_json()
    pairs = ast.literal_eval(data.get('pairs'))
    username = data.get('username')
    id = data.get('id')

    pair_ids = db.execute("""SELECT id FROM person_details 
                            WHERE username = ? AND status = 0 AND NOT id = ?""", 
                            username, id)
    pair_ids = [row['id'] for row in pair_ids]

    # pair accept - gửi cho user match result
    db.execute("""UPDATE matches SET pair_accept_status = 2
                  WHERE pair_details_id = ? AND user_details_id = ?""",
                  pairs[0], pairs[1])

    return "Success", 200


@app.route('/contact', methods=['GET','POST'])
def contact():
    data = request.get_json()
    person_details_id = data.get('person_details_id')

    info = db.execute("SELECT name, mail FROM person_details WHERE id = ?", person_details_id)

    if not info:
        return "Something went wrong", 403
    
    return {'info':info}


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
        updated_embeds = np.vstack((old_embeds, embed))
    if updated_embeds is not None:
        np.save('users.npy', updated_embeds)

    # pickle mapping
    mapping.append(int(person_details_id))

    with open('users.pkl', 'wb') as f:
        pickle.dump(mapping, f)

    return {'person_details_id':person_details_id}


@app.route('/portfolio', methods=['GET'])
def portfolio_get():
    data = request.get_json()
    id = data.get('person_details_id')
    username = data.get('username')

    photo_path = db.execute(""" SELECT photo_path
                                FROM images
                                JOIN person_details ON images.id = person_details.img_id
                                WHERE person_details.id = ?""", id)
    
    person_details = db.execute(""" SELECT p.*, u.find_me
                                    FROM person_details p
                                    JOIN users u ON u.person_details_id = p.id
                                    WHERE id = ?""", id)
    
    photo_path = photo_path[0]['photo_path'] if photo_path else None

    history = db.execute("""SELECT * FROM matches m
                            JOIN person_details p ON p.id = m.pair_details_id 
                            OR p.id = m.user_details_id
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

