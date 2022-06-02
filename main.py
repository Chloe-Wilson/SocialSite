import os
import sqlite3
import random
import string

from flask import Flask, request, render_template, redirect, url_for, make_response

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './Static'


def checkCred():
    conn = sqlite3.connect('login')
    crsr = conn.cursor()
    crsr.execute(
        'SELECT 1 FROM login WHERE name = "' + request.cookies.get('user', "") + '" AND key = "' + request.cookies.get(
            'key', "") + '";')
    data = crsr.fetchall()
    conn.commit()
    conn.close()
    if data:
        return 1
    else:
        return 0


@app.route("/", methods=['GET', 'POST'])
def front():
    if request.method == 'POST':
        if request.form.get('Login') == 'login':
            return redirect(url_for('login'))
        elif request.form.get('Sign Up') == 'signup':
            return redirect(url_for('signup'))
    return render_template('front.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = sqlite3.connect('login')
        crsr = conn.cursor()
        crsr.execute(
            'SELECT 1 FROM login WHERE name = "' + request.form.get('Username') + '" AND pass = "' + request.form.get(
                'Password') + '";')
        data = crsr.fetchall()
        conn.commit()
        conn.close()
        if data:
            resp = make_response(redirect(url_for('home')))
            resp.set_cookie('user', request.form.get('Username'))

            conn = sqlite3.connect('login')
            crsr = conn.cursor()
            key = (''.join(random.choice(string.ascii_letters) for i in range(50)))
            crsr.execute('UPDATE login SET key ="' + key + '" WHERE name = "' + request.form.get('Username') + '";')
            resp.set_cookie('key', key)
            conn.commit()
            conn.close()

            return resp
        else:
            return '<p>Username or Password Wrong</p>' + render_template('login.html')
    else:
        conn = sqlite3.connect('login')
        crsr = conn.cursor()
        crsr.execute(
            'SELECT 1 FROM login WHERE name = "' + request.cookies.get('user', "") + '" AND key = "' + request.cookies.get('key', "") + '";')
        data = crsr.fetchall()
        conn.commit()
        conn.close()
        if data:
            return redirect(url_for('home'))
        else:
            return render_template('login.html')


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        conn = sqlite3.connect('login')
        crsr = conn.cursor()
        crsr.execute('SELECT 1 FROM login WHERE name = "' + request.form.get('Username') + '";')
        data = crsr.fetchall()
        print(data)
        if data:
            conn.commit()
            conn.close()
            return '<p>Username Taken</p>' + render_template('signup.html')
        elif request.form.get('Password') != request.form.get('Repeat Password'):
            conn.commit()
            conn.close()
            return '<p>Passwords not the same</p>' + render_template('signup.html')
        else:
            key = (''.join(random.choice(string.ascii_letters) for i in range(50)))
            crsr.execute('INSERT INTO login VALUES ("' + request.form.get('Username') + '", "' + request.form.get(
                'Password') + '", "' + key + '")')
            conn.commit()
            conn.close()

            conn = sqlite3.connect('Accounts/' + request.form.get('Username'))
            crsr = conn.cursor()
            crsr.execute('CREATE TABLE follow (user varchar(255));')
            crsr.execute('INSERT INTO follow (user) VALUES ("' + request.form.get('Username') + '");')
            conn.commit()
            conn.close()

            resp = make_response(redirect(url_for('home')))
            resp.set_cookie('user', request.form.get('Username'))
            resp.set_cookie('key', key)
            return resp

    return render_template('signup.html')


@app.route("/upload", methods=['GET', 'POST'])
def upload():
    if not checkCred():
        resp = make_response(redirect(url_for('front')))
        resp.set_cookie('user', '')
        resp.set_cookie('key', '')
        return resp
    if request.method == 'POST':
        f = request.files['file']
        if f:
            conn = sqlite3.connect('login')
            crsr = conn.cursor()
            id = len(os.listdir('./Static/'))
            crsr.execute('INSERT INTO posts (id, cap, user) VALUES ("' + str(id) + '.png", "' + request.form.get(
                'Caption') + '", "' + request.cookies.get('user', "") + '");')
            conn.commit()
            conn.close()
            f.save('Static/' + str(id) + '.png')

            return redirect(url_for('home'))
        else:
            return '<p>No File</p>' + render_template('upload.html')
    else:
        return render_template('upload.html')


@app.route("/Home/", methods=['GET', 'POST'])
def home():
    if not checkCred():
        resp = make_response(redirect(url_for('front')))
        resp.set_cookie('user', '')
        resp.set_cookie('key', '')
        return resp
    if request.method == 'POST':
        if request.form.get('logout') == 'logout':
            resp = make_response(redirect(url_for('front')))
            resp.set_cookie('user', '')
            resp.set_cookie('key', '')
            return resp
        if request.form.get('upload') == 'upload':
            return redirect(url_for('upload'))
        if request.form.get('search') == 'search':
            return redirect(url_for('account', name=request.form.get('searchBox')))
    else:
        conn = sqlite3.connect('Accounts/' + request.cookies.get('user', ""))
        crsr = conn.cursor()
        crsr.execute('SELECT * FROM follow;')
        following = crsr.fetchall()
        conn.commit()
        conn.close()

        conn = sqlite3.connect('login')
        crsr = conn.cursor()
        req = 'SELECT * FROM posts WHERE user IN ("'
        for name in following:
            req += name[0] + '", "'
        req += '") ORDER BY date DESC;'
        crsr.execute(req)
        data = crsr.fetchall()
        conn.commit()
        conn.close()

        resp = render_template('home.html')
        for post in data:
            resp = resp + render_template('img.html', img=url_for('static', filename=post[0]), caption=post[1])
        return resp


@app.route('/Account/<name>', methods=['GET', 'POST'])
def account(name):
    if not checkCred():
        resp = make_response(redirect(url_for('front')))
        resp.set_cookie('user', '')
        resp.set_cookie('key', '')
        return resp
    if request.method == 'POST':
        if request.form.get("Home") == 'Home':
            return redirect(url_for('home'))
        if request.form.get("Follow") == 'Follow':
            conn = sqlite3.connect('Accounts/' + request.cookies.get('user', ""))
            crsr = conn.cursor()
            crsr.execute('INSERT INTO follow (user) VALUES ("' + name + '");')
            conn.commit()
            conn.close()
            return redirect(url_for('account', name=name))
        elif request.form.get("Follow") == 'Unfollow':
            conn = sqlite3.connect('Accounts/' + request.cookies.get('user', ""))
            crsr = conn.cursor()
            crsr.execute('DELETE FROM follow WHERE user = "' + name + '";')
            conn.commit()
            conn.close()
            return redirect(url_for('account', name=name))
    else:
        conn = sqlite3.connect('Accounts/' + request.cookies.get('user', ""))
        crsr = conn.cursor()
        crsr.execute('SELECT 1 FROM follow WHERE user = "' + name + '";')
        following = crsr.fetchall()
        conn.commit()
        conn.close()
        if following:
            resp = render_template('follow.html', button="Unfollow", name=name)
        else:
            resp = render_template('follow.html', button="Follow", name=name)

        conn = sqlite3.connect('login')
        crsr = conn.cursor()
        req = 'SELECT * FROM posts WHERE user = "' + name + '" ORDER BY date DESC;'
        crsr.execute(req)
        data = crsr.fetchall()
        conn.commit()
        conn.close()
        for post in data:
            resp = resp + render_template('img.html', img=url_for('static', filename=post[0]), caption=post[1])
        return resp

# conn = sqlite3.connect('login')
# crsr = conn.cursor()
# crsr.execute('DROP TABLE IF EXISTS login;')
# crsr.execute('DROP TABLE IF EXISTS posts;')
# crsr.execute('CREATE TABLE login (name varchar(255), pass varchar(255), key varchar(255));')
# crsr.execute(
#     'CREATE TABLE posts (id varchar(255), cap varchar(255), user varchar(255), date TIMESTAMP NOT NULL DEFAULT '
#     'CURRENT_TIMESTAMP);')
# conn.commit()
# conn.close()

# conn = sqlite3.connect('login')
# crsr = conn.cursor()
# crsr.execute('INSERT INTO posts (id, cap, user) VALUES ("' + str(0) + '.png", "AA", "Billy");')
# crsr.execute('SELECT * FROM posts WHERE user IN ("Billy");')
# print(crsr.fetchall())
# conn.commit()
# conn.close()
