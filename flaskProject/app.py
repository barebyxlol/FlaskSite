import flask
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, send_file
import sqlite3
import os
import pdfkit

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='admin'))

app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('scheme.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.route('/myresumes')
def show_entries():
    db = get_db()
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    cur = db.execute('select * from resumes where user_id = (?) order by id desc', [session.get('user_id')])
    entries = cur.fetchall()
    username = db.execute('select username from users where id = (?)', [session.get('user_id')]).fetchone()[0]
    return render_template('show_entries.html', entries=entries, username=username)


@app.route('/add', methods=['GET', 'POST'])
def add_resume():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    username = db.execute('select username from users where id = (?)', [session.get('user_id')]).fetchone()[0]
    if request.method == "POST":
        db.execute(
            'insert into resumes (user_id, title, employer, experience, skills, relevant_info) values (?, ?, ?, ?, ?, ?)',
            [session['user_id'], request.form['title'], request.form['employer'], request.form['experience'],
             request.form['skills'], request.form['relevant_info']])
        db.commit()
        flash('New resume was successfully added')
        return redirect(url_for('show_entries', username=username))
    else:
        name = db.execute('select name from users where id = (?)', [session['user_id']]).fetchone()[0]
        surname = db.execute('select surname from users where id = (?)', [session['user_id']]).fetchone()[0]
        last_name = db.execute('select last_name from users where id = (?)', [session['user_id']]).fetchone()[0]
        return render_template('add_entry.html', name=name, surname=surname, last_name=last_name, username=username)


@app.route('/')
def start():
    db = get_db()
    if session.get('user_id'):
        username = db.execute('select username from users where id = (?)', [session.get('user_id')]).fetchone()[0]
    else:
        username = None

    return render_template('layout.html', username=username)


@app.route('/usr/<username>/', methods=['GET', 'POST'])
def show_user_profile(username):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    if request.method == "POST":
        if db.execute('select username from users where id = (?)', [session['user_id']]).fetchone()[0] != username:
            username1 = db.execute('select username from users where id = (?)', [session['user_id']]).fetchone()[0]
            return render_template('forbidden.html', username=username1), 403
        else:
            if request.form['name'] == '':
                n = db.execute('select name from users where id = (?)', [session['user_id']]).fetchone()[0]
            else:
                n = request.form['name']
            if request.form['surname'] == '':
                s = db.execute('select surname from users where id = (?)', [session['user_id']]).fetchone()[0]
            else:
                s = request.form['surname']
            if request.form['last_name'] == '':
                l = db.execute('select last_name from users where id = (?)', [session['user_id']]).fetchone()[0]
            else:
                l = request.form['last_name']
            db.execute("update users set name = (?), surname = (?), last_name = (?) where id = (?)", [n, s, l, session['user_id']])
            db.commit()
            return redirect(url_for('show_user_profile', username=username))
    if db.execute('select username from users where username = (?)', [username]).fetchone():
        if db.execute('select username from users where id = (?)', [session['user_id']]).fetchone()[0] != username:
            name = db.execute('select name from users where username = (?)', [username]).fetchone()[0]
            surname = db.execute('select surname from users where username = (?)', [username]).fetchone()[0]
            last_name = db.execute('select last_name from users where username = (?)', [username]).fetchone()[0]
            username1 = db.execute('select username from users where id = (?)', [session['user_id']]).fetchone()[0]
            return render_template('show_user_profile.html', name=name, surname=surname, last_name=last_name,
                                   username=username1)
        else:
            name = db.execute('select name from users where id = (?)', [session['user_id']]).fetchone()[0]
            surname = db.execute('select surname from users where id = (?)', [session['user_id']]).fetchone()[0]
            last_name = db.execute('select last_name from users where id = (?)', [session['user_id']]).fetchone()[0]
            return render_template('my_user_profile.html', name=name, surname=surname, last_name=last_name,
                                   username=username)
    else:
        username1 = db.execute('select username from users where id = (?)', [session['user_id']]).fetchone()[0]
        return render_template('page_not_found.html', username=username1)


@app.route('/post/<int:post_id>/', methods=["GET", "POST"])
def show_post(post_id):
    if not session['logged_in']:
        return redirect(url_for('login'))
    db = get_db()
    if db.execute('select user_id from resumes where id = (?)', [post_id]).fetchone():
        if db.execute('select user_id from resumes where id = (?)', [post_id]).fetchone()[0] != session['user_id']:
            username = db.execute('select username from users where id = (?)', [session['user_id']]).fetchone()[0]
            return render_template('forbidden.html', username=username), 403
        name = db.execute('select name from users where id = (?)', [session['user_id']]).fetchone()[0]
        surname = db.execute('select surname from users where id = (?)', [session['user_id']]).fetchone()[0]
        last_name = db.execute('select last_name from users where id = (?)', [session['user_id']]).fetchone()[0]
        username = db.execute('select username from users where id = (?)', [session['user_id']]).fetchone()[0]
        title = db.execute('select title from resumes where id = (?)', [post_id]).fetchone()[0]
        employer = db.execute('select employer from resumes where id = (?)', [post_id]).fetchone()[0]
        experience = db.execute('select experience from resumes where id = (?)', [post_id]).fetchone()[0]
        skills = db.execute('select skills from resumes where id = (?)', [post_id]).fetchone()[0]
        relevant_info = db.execute('select relevant_info from resumes where id = (?)', [post_id]).fetchone()[0]
    else:
        username = db.execute('select username from users where id = (?)', [session['user_id']]).fetchone()[0]
        return render_template('page_not_found.html', username=username)
    if request.method == "POST":
        options = {'encoding': "UTF-8"}
        pdfkit.from_string(
            render_template('dwnld_resume.html', name=name, surname=surname, last_name=last_name, username=username,
                            title=title, experience=experience, employer=employer, skills=skills,
                            relevant_info=relevant_info, post_id=post_id), 'out.pdf', css='./static/style2.css',
            options=options)
        return send_file('out.pdf', as_attachment=True, download_name='resume_for_{}'.format(employer))

    return render_template('show_resume.html', name=name, surname=surname, last_name=last_name, username=username,
                           title=title, experience=experience, employer=employer, skills=skills,
                           relevant_info=relevant_info, post_id=post_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    db = get_db()
    if session.get('logged_in', None):
        return redirect(url_for('start'))
    if request.method == 'POST':
        if len(db.execute('select username from users where username = (?)',
                          [request.form['username']]).fetchall()) != 1:
            error = 'Invalid username or password'
        elif db.execute('select password from users where username = (?)', [request.form['username']]).fetchone()[0] != \
                request.form['password']:
            error = 'Invalid username or password'
        else:
            session['logged_in'] = True
            session['user_id'] = \
                db.execute('select id from users where username = (?)', [request.form['username']]).fetchone()[0]
            flash('You were logged in')
            return redirect(url_for('show_entries', username=request.form['username']))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    session['logged_in'] = False
    return redirect(url_for('start'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    db = get_db()
    if session.get('logged_in'):
        return redirect(url_for('start'))
    if request.method == "POST":
        if len(db.execute('select username from users where username = (?)',
                          [request.form['username']]).fetchall()) > 0:
            error = 'This username is already taken, choose another'
        elif request.form['password'] != request.form['password2']:
            error = "Passwords don't match"
        else:
            db.execute('insert into users (username, password) values (?, ?)',
                       [request.form['username'], request.form['password']])
            db.commit()
            session['logged_in'] = True
            session['user_id'] = \
                db.execute('select id from users where username = (?)', [request.form['username']]).fetchone()[0]
            flash("Account successfully created")
            return redirect(url_for('show_entries', username=request.form['username']))

    return render_template("register.html", error=error)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
