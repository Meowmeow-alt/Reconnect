from flask import Flask, render_template, redirect, request, session, flash
from werkzeug.utils import secure_filename
import os
from flask_session import Session
import uuid
import json
import requests
from addition import login_required


app = Flask(__name__)
app.config['SECRET_KEY'] = 'for something secretive'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


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

        res = requests.post('http://127.0.0.1:5001/login', json={'username':username, 'password':password})

        if res.status_code == 403 or res.status_code == 500:
            flash(res.text)
            return redirect(request.url)
        
        rows = res.json()['rows']

        if rows['person_details_id'] is None:
            return redirect('/personal')

        session["username"] = username
        session['person_details_id'] = rows['person_details_id']
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
        
        res = requests.post('http://127.0.0.1:5001/register', json={'username':username, 'password':password})

        if res.status_code == 403 or res.status_code == 500:
            flash(res.text)
            return redirect(request.url)

        session["username"] = username
        return redirect('/personal')

    return render_template('register.html')


@app.route('/personal', methods=['GET', 'POST'])
def personal():
    if request.method == 'POST':
        name = request.form.get('name').title().strip()

        age = request.form.get('age')
        if not age or int(age) not in range(1,180):
            flash('Age Invalid')
            return redirect(request.url)
        age = int(age)

        city = request.form.get('city')
        if not city:
            flash('City Invalid')
            return redirect(request.url)
        city = int(city)

        sex = request.form.get('sex')
        if not sex:
            flash('Gender Invalid')
            return redirect(request.url)
        sex = 0 if str(sex).lower() == 'female' else 1

        height = request.form.get('height')
        if not height:
            flash('Height Invalid')
            return redirect(request.url)
        height = int(height)

        marks = request.form.get('marks')

        phone = request.form.get('phone')
        if not phone or phone.isdigit() == False or len(phone) > 12 or len(phone) < 10:
            flash('Invalid phone number')
            return redirect(request.url)

        mail = request.form.get('mail').lower()
        if not mail or '@' not in mail or '.' not in mail:
            flash('Invalid email address')
            return redirect(request.url)
        
        res = requests.post('http://127.0.0.1:5001/personal', json={'username':session["username"], 'name':name, 'age':age,\
                                        'city':city, 'sex':sex, 'height':height, 'marks':marks, 'phone':phone, 'mail':mail})

        data = res.json()
        session['person_details_id'] = data['person_details_id']
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
    if request.method == 'POST':
        # Photo
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
            
        file = request.files['file']

        if not file or file.filename == '' or not file.filename.lower().endswith(('.jpeg', '.png', '.jpg')):
            flash('File Invalid')
            return redirect(request.url)

        #  Info
        name = request.form.get('name').title().strip()
        if not name:
            flash('There must be a name')
            return redirect(request.url)

        age = request.form.get('age')
        if not age or int(age) not in range(1,180):
            flash('Age Invalid')
            return redirect(request.url)
        age = int(age)
        
        marks = request.form.get('marks')

        sex = request.form.get('sex')
        if not sex:
            flash('Gender Invalid')
            return redirect(request.url)
        sex = 0 if str(sex).lower() == 'female' else 1

        city = request.form.get('city')
        if not city:
            flash('City Invalid')
            return redirect(request.url)
        city = int(city)

        height = request.form.get('height')
        if not height:
            flash('Height Invalid')
            return redirect(request.url)
        height = int(height)

        last_seen = request.form.get('last')
        if not last_seen or len(str(last_seen)) != 4 or int(last_seen) < 1700:
            flash('Year Invalid format yyyy')
            return redirect(request.url)
        last_seen = int(last_seen)

        phone, mail = 'None', 'None'

        relate = request.form.get('relate')
        if not relate:
            flash('Relationship must be set')
            return redirect(request.url)
        
        # Post to backend
        files = {
            'img': (file.filename, file, file.mimetype),
            'relate': (None, str(relate)),
            'username': (None, str(session["username"])),
            'name': (None, str(name)),
            'age': (None, str(age)),
            'city': (None, str(city)),
            'sex': (None, str(sex)),
            'height': (None, str(height)),
            'marks': (None, str(marks)),
            'phone': (None, str(phone)),
            'mail': (None, str(mail)),
            'last_seen': (None, str(last_seen)),
        }
        
        res = requests.post('http://127.0.0.1:5001/search', files=files)

        if res.status_code == 403 or res.status_code == 500:
            flash(res.text)
            return redirect(request.url)
        
        return redirect(request.url)
    
    with open('json/location.json', 'r') as f:
        location = json.load(f)
    with open('json/height.json', 'r') as f:
        height = json.load(f)

    res = requests.get('http://127.0.0.1:5001/search', json={'username': session["username"]})
    data = res.json()
    for person in data['people']:
        person['photo_path'] = "http://127.0.0.1:5001/get_image?photo_path=" + person['photo_path']

    return render_template('search.html', location=location, height=height, people=data['people'])


@app.route('/delete', methods=['POST'])
@login_required
def delete():
    id = request.form.get('id')
    photo_path = request.form.get('photo_path')
    res = requests.post('http://127.0.0.1:5001/delete', json={'id':id, 'photo_path':photo_path})

    if res.status_code == 403 or res.status_code == 500:
        flash(res.text)
        return redirect(request.url)
    
    return redirect('/search')


@app.route('/result', methods=['GET'])
@login_required
def result():
    res = requests.get('http://127.0.0.1:5001/result', json={'username': session["username"]})
    
    if res.status_code == 403 or res.status_code == 500:
        flash(res.text)
        return render_template('result.html')
    
    try:
        data = res.json()
    except requests.exceptions.JSONDecodeError:
        flash("No data to decode")
        return render_template('result.html')
    
    for person in data['user']:
        person['photo_path'] = "http://127.0.0.1:5001/get_image?photo_path=" + person['photo_path']
    for person in data['pair']:
        person['photo_path'] = "http://127.0.0.1:5001/get_image?photo_path=" + person['photo_path']
    
    return render_template('result.html', user=data['user'], pair=data['pair'])


@app.route('/decline', methods=['POST'])
@login_required
def decline():
    # id = request.form.get('id')
    # photo_path = request.form.get('photo_path')
    # res = requests.post('http://127.0.0.1:5001/delete', json={'id':id, 'photo_path':photo_path})

    # if res.status_code == 403 or res.status_code == 500:
    #     flash(res.text)
    #     return redirect(request.url)
    
    return redirect('/result')


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

        if not file or file.filename == '' or not file.filename.lower().endswith(('.jpeg', '.png', '.jpg')):
            flash('File Invalid')
            return redirect(request.url)

        files = {
            'img': (file.filename, file, file.mimetype),
            'person_details_id': (None, str(session['person_details_id']))
        }
        res = requests.post('http://127.0.0.1:5001/portfolio', files=files)

        session['person_details_id'] = res.json()['person_details_id']
        return redirect(request.url)

    res = requests.get('http://127.0.0.1:5001/portfolio', json={'username':session["username"], 'person_details_id': session['person_details_id']})
    
    data = res.json()
    session['photo_path'] = data['photo_path']
    default_profile =  'https://img.myloview.com/stickers/default-avatar-profile-icon-vector-social-media-user-photo-700-205577532.jpg'
    photo_path = "http://127.0.0.1:5001/get_image?photo_path=" + data['photo_path'] if data['photo_path'] else default_profile

    return render_template('portfolio.html', photo_path=photo_path, details=data['details'], history=data['history'])


@app.route('/findme', methods=['GET','POST'])
@login_required
def findme():
    res = requests.post('http://127.0.0.1:5001/findme', json={'person_details_id':session['person_details_id'], 'photo_path': session['photo_path']})
    
    if res.status_code == 403 or res.status_code == 500:
        flash(res.text)

    return redirect('/portfolio')


@app.route('/disable_findme', methods=['GET','POST'])
@login_required
def disable_findme():
    requests.post('http://127.0.0.1:5001/disable_findme', json={'username':session['username']})
    return redirect('/portfolio')



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


