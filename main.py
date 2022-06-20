import os
import random
import sqlite3
import string
import json

import numpy as np
from flask import Flask, Response, request, render_template, redirect, url_for, make_response
from Levenshtein import distance

reserved = ['MrPlane']

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './static'


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
    return render_template('head.html') + render_template('front.html')


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
            return render_template('head.html') + '<p>Username or Password Wrong</p>' + render_template('login.html')
    else:
        conn = sqlite3.connect('login')
        crsr = conn.cursor()
        crsr.execute(
            'SELECT 1 FROM login WHERE name = "' + request.cookies.get('user',
                                                                       "") + '" AND key = "' + request.cookies.get(
                'key', "") + '";')
        data = crsr.fetchall()
        conn.commit()
        conn.close()
        if data:
            return redirect(url_for('home'))
        else:
            return render_template('head.html') + render_template('login.html')


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if request.form.get('Username') in reserved:
            return render_template(
                'head.html') + '<p>Name reserved. Try searching once signed up</p>' + render_template('signup.html')
        if not all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789' for c in
                   request.form.get('Username')):
            return render_template(
                'head.html') + '<p>Invalid Characters in Username. Valid(A:Z, a:z, 0:9)</p>' + render_template(
                'signup.html')
        if not all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-_!@#$%^&*' for c in
                   request.form.get('Password')):
            return render_template(
                'head.html') + '<p>Invalid Characters in Password. Valid(A:Z, a:z, 0:9, ._-!@#$%^&*)</p>' + render_template(
                'signup.html')
        conn = sqlite3.connect('login')
        crsr = conn.cursor()
        crsr.execute('SELECT 1 FROM login WHERE name = "' + request.form.get('Username') + '";')
        data = crsr.fetchall()
        print(data)
        if data:
            conn.commit()
            conn.close()
            return render_template('head.html') + '<p>Username Taken</p>' + render_template('signup.html')
        elif request.form.get('Password') != request.form.get('Repeat Password'):
            conn.commit()
            conn.close()
            return render_template('head.html') + '<p>Passwords not the same</p>' + render_template('signup.html')
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

    return render_template('head.html') + render_template('signup.html')


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
            id = len(os.listdir('static/'))
            crsr.execute('INSERT INTO posts (id, cap, user) VALUES ("' + str(id) + '.png", "' + request.form.get(
                'Caption') + '", "' + request.cookies.get('user', "") + '");')
            conn.commit()
            conn.close()
            f.save('static/' + str(id) + '.png')

            return redirect(url_for('home'))
        else:
            return render_template('head.html') + '<p>No File</p>' + render_template('upload.html')
    else:
        return render_template('head.html') + render_template('upload.html')


@app.route('/_autocomplete', methods=['GET'])
def autocomplete():
    conn = sqlite3.connect('login')
    crsr = conn.cursor()
    crsr.execute('SELECT name FROM login')
    usernames = crsr.fetchall()
    conn.commit()
    conn.close()
    users = []
    for name in usernames:
        users.append(name[0])
    return Response(json.dumps(users), mimetype='application/json')


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
            if request.form.get('searchBox') in reserved:
                return redirect(url_for(request.form.get('searchBox')))
            else:
                conn = sqlite3.connect('login')
                crsr = conn.cursor()
                crsr.execute('SELECT name FROM login')
                users = crsr.fetchall()
                conn.commit()
                conn.close()
                minU = 0
                userC = request.form.get('searchBox')
                minV = distance(users[0][0], userC)
                for i in range(len(users)):
                    if distance(users[i][0], userC) < minV:
                        minV = distance(users[i][0], userC)
                        minU = i
                return redirect(url_for('account', name=users[minU][0]))
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
        crsr.execute('SELECT name FROM login')
        usernames = crsr.fetchall()
        conn.close()
        resp = render_template('head.html') + '<body class="background">' + render_template('nameplate.html', name="Dashboard") + render_template('home.html')
        resp += '<datalist id="names">'
        for name in usernames:
            resp += '<option value="' + name[0] + '">'
        resp += '</datalist>'
        for post in data:
            if post[2] == request.cookies.get('user', ''):
                resp = resp + render_template('img.html', img=url_for('static', filename=post[0]), caption=post[1], name=post[2], likes=post[3], page="home", show="visible")
            else:
                resp = resp + render_template('img.html', img=url_for('static', filename=post[0]), caption=post[1], name=post[2], likes=post[3], page="home", show="hidden")
        resp += '</body>'
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
        resp = render_template('head.html') + '<body class="background">' + render_template('nameplate.html', name=name)
        if following:
            resp += render_template('follow.html', button="Unfollow", name=name)
        else:
            resp += render_template('follow.html', button="Follow", name=name)

        conn = sqlite3.connect('login')
        crsr = conn.cursor()
        req = 'SELECT * FROM posts WHERE user = "' + name + '" ORDER BY date DESC;'
        crsr.execute(req)
        data = crsr.fetchall()
        conn.commit()
        conn.close()
        for post in data:
            if post[2] == request.cookies.get('user', ''):
                resp = resp + render_template('img.html', img=url_for('static', filename=post[0]), caption=post[1], name=post[2], likes=post[3], page=name, show="visible")
            else:
                resp = resp + render_template('img.html', img=url_for('static', filename=post[0]), caption=post[1], name=post[2], likes=post[3], page=name, show="hidden")
        resp += '</body>'
        return resp


@app.route('/delete', methods=['POST'])
def delete():
    conn = sqlite3.connect('login')
    crsr = conn.cursor()
    if request.form.get('delete'):
        crsr.execute('DELETE FROM posts WHERE id="' + request.form.get('delete').split('/')[2] + '" and user="' + request.cookies.get('user', '') + '";')
    elif request.form.get('like'):
        crsr.execute('UPDATE posts SET likes=likes+1 WHERE id="' + request.form.get('like').split('/')[2] + '";')
    conn.commit()
    conn.close()
    if request.form.get('page') == 'home':
        return redirect(url_for('home'))
    else:
        return redirect(url_for('account', name=request.form.get('page')))


def drawPlane(board, plane, msg=""):
    if not msg == "Previous Shot":
        x = {1: 0, 2: 1, 3: 0, 4: -1}
        y = {1: -1, 2: 0, 3: 1, 4: 0}
        direction = random.randint(1, 4)
        stuck = 0
        while stuck < 4:
            stuck += 1
            xm = min(max(plane[0] + x.get(direction), 0), len(board) - 1)
            ym = min(max(plane[1] + y.get(direction), 0), len(board[0]) - 1)
            if not board[xm][ym]:
                plane = xm, ym
                np.savetxt('tmp/plane_pos_' + request.cookies.get('user', ""), plane, delimiter=',', fmt='%d')
                break
            direction += 1
            if direction > 4:
                direction = 1
    if msg != "Hit":
        resp = '<form method="post" action="/MrPlane">'
    else:
        resp = '<form>'
    for j in range(len(board[0])):
        for i in range(len(board)):
            if board[i][j]:
                resp += '<input type="submit" value="' + str(i) + ',' + str(
                    j) + '" name="Enter" style="color:red; background-color:red; width:' + str(
                    100 / len(board)) + '%; height:' + str(100 / len(board[0])) + '%">'
            else:
                resp += '<input type="submit" value="' + str(i) + ',' + str(
                    j) + '" name="Enter" style="color:white; width:' + str(100 / len(board)) + '%; height:' + str(
                    100 / len(board[0])) + '%">'
    resp += '</form><p>' + msg + '</p>'
    return resp


@app.route('/MrPlane', methods=['GET', 'POST'])
def MrPlane():
    if request.method == 'POST':
        if request.form.get('Enter') == 'Enter':
            if int(request.form.get('Rows')) > 0 and int(request.form.get('Columns')) > 0:
                board = np.zeros((min(int(request.form.get('Rows')), 50), min(int(request.form.get('Columns')), 50)),
                                 dtype=int)
                planePos = [random.randint(0, len(board) - 1), random.randint(0, len(board[0]) - 1)]
                np.savetxt('./tmp/plane_board_' + request.cookies.get('user', ""), board, delimiter=',', fmt='%d')
                return drawPlane(board, planePos)
        elif request.form.get('Enter') == 'Home':
            try:
                os.remove('tmp/plane_board_' + request.cookies.get('user', ""))
                os.remove('tmp/plane_pos_' + request.cookies.get('user', ""))
            except:
                pass
            return redirect(url_for('home'))
        elif request.form.get('Enter'):
            x, y = request.form.get('Enter').split(',')
            x = int(x)
            y = int(y)
            board = np.genfromtxt('tmp/plane_board_' + request.cookies.get('user', ""), delimiter=',', dtype=int,
                                  encoding='UTF-8')
            planePos = np.genfromtxt('tmp/plane_pos_' + request.cookies.get('user', ""), delimiter=',', dtype=int,
                                     encoding='UTF-8')
            if board[x][y]:
                return drawPlane(board, planePos, "Previous Shot")
            board[x][y] = 1
            np.savetxt('tmp/plane_board_' + request.cookies.get('user', ""), board, delimiter=',', fmt='%d')
            if x == planePos[0] and y == planePos[1]:
                return drawPlane(board, planePos, "Hit")
            else:
                if x == planePos[0]:
                    if y > planePos[1]:
                        return drawPlane(board, planePos, "Dew North")
                    else:
                        return drawPlane(board, planePos, "Dew South")
                elif y == planePos[1]:
                    if x > planePos[0]:
                        return drawPlane(board, planePos, "Dew West")
                    else:
                        return drawPlane(board, planePos, "Dew East")
                else:
                    lx = planePos[0] - x
                    ly = planePos[1] - y
                    if abs(lx) > abs(ly):
                        if lx > 0:
                            return drawPlane(board, planePos, "Eastish")
                        else:
                            return drawPlane(board, planePos, "Westish")
                    elif abs(lx) < abs(ly):
                        if ly > 0:
                            return drawPlane(board, planePos, "Southish")
                        else:
                            return drawPlane(board, planePos, "Nothish")
                    else:
                        if lx > 0:
                            if ly > 0:
                                return drawPlane(board, planePos, "South East")
                            else:
                                return drawPlane(board, planePos, "North East")
                        else:
                            if ly > 0:
                                return drawPlane(board, planePos, "South West")
                            else:
                                return drawPlane(board, planePos, "North West")


    else:
        return render_template('planeSetup.html')

# conn = sqlite3.connect('login')
# crsr = conn.cursor()
# crsr.execute('DROP TABLE IF EXISTS login;')
# crsr.execute('DROP TABLE IF EXISTS posts;')
# crsr.execute('CREATE TABLE login (name varchar(255), pass varchar(255), key varchar(255));')
# crsr.execute(
#     'CREATE TABLE posts (id varchar(255), cap varchar(255), user varchar(255), likes int DEFAULT 0, date TIMESTAMP NOT NULL DEFAULT '
#     'CURRENT_TIMESTAMP);')
# conn.commit()
# conn.close()

