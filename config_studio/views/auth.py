from flask import request
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms import BooleanField
from wtforms.validators import DataRequired, ValidationError
import json
import xlrd
from pathlib import Path
from werkzeug.utils import secure_filename
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import widgets
from config_studio import db, mail
from .model import User
from .forms import LoginForm, CommentForm, ContactForm
from flask import make_response, flash
from flask import g
import requests
from flask_mail import Message
from functools import wraps


GOOGLE_RECAPTCHA_SECRET_KEY = '6LfGgaQZAAAAALFg29Ktye6qiinyqwIhj-xqmYO5'

URL = 'https://recaptcha.net/recaptcha/api/siteverify'

headers = {'content-type': 'application/json'}
auth = Blueprint('auth', __name__)


def check_recaptcha(f):
    """
    Checks Google  reCAPTCHA.

    :param f: view function
    :return: Function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request.recaptcha_is_valid = None

        if request.method == 'POST':
            data = {
                'secret': GOOGLE_RECAPTCHA_SECRET_KEY,
                'response': request.form['g-recaptcha-response'],
                'remoteip': request.access_route[0]
            }
            r = requests.post(
                URL,
                data=data
            )
            result = r.json()

            if result['success']:
                request.recaptcha_is_valid = True
            else:
                request.recaptcha_is_valid = False
                flash('Invalid reCAPTCHA. Please try again.', 'error')

        return f(*args, **kwargs)

    return decorated_function


@auth.route('/login', methods=['GET', 'POST'], endpoint='login')
def login():
    form = LoginForm()
    if request.method == 'POST':
        try:
            # if form.validate_on_submit():
                username = request.form['username']
                password = request.form['password']
                user = User.query.filter_by(username=username).first_or_404(
                    description='THE {} is not found'.format(username))

                response = request.form['g-recaptcha-response']
                data = {
                    'secret': GOOGLE_RECAPTCHA_SECRET_KEY,
                    'response': response,
                }
                res = requests.post(URL, data=data)

                if user.username == username and user.password == password and res.json()['success']:
                    session['username'] = request.form['username']
                    flash('You were successfully logged in', 'sucess')
                    return redirect(url_for('index'))
                else:
                    error_msg = '登陆失败!用户名或密码错误'
                    return render_template('auth/login.html', error_msg=error_msg, form=form)

        except Exception as e:
            error_msg = '验证失败'
            print(str(e), '-----------')
            return render_template('auth/login.html', form=form, error_msg=error_msg)
    return render_template('auth/login.html', form=form)


@auth.route('/sign', methods=['GET', 'POST'], endpoint='sign')
def sign():
    if request.method == 'POST':
        response = request.form['g-recaptcha-response']
        data = {
            'secret': GOOGLE_RECAPTCHA_SECRET_KEY,
            'response': response,
        }
        r = requests.post(
            URL,
            data=data
        )
        result = r.json()
        print(response, result)
        return 'hello'

    return render_template('auth/sign.html')


@auth.route('/logout', endpoint='logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    # return redirect(url_for('home.index'))
    return render_template('auth/logout.html')


@auth.route('/get_cookie', methods=['GET', 'POST'], endpoint='get_cookie')
def get_cookie():
    username = request.cookies.get('username')
    # use cookies.get(key) instead of cookies[key] to not get a
    # KeyError if the cookie is missing.


@auth.route('/set_cookie', methods=['GET', 'POST'], endpoint='set_cookie')
def set_cookie():
    resp = make_response(render_template(...))
    resp.set_cookie('username', 'the username')
    return resp


@auth.route("/comment", methods=['GET', 'POST'], endpoint='comment')
def index(form=None):
    if form is None:
        form = CommentForm()
    comments = session.get("comments", [])
    return render_template("auth/comment.html",
                           comments=comments,
                           form=form)


@auth.route("/add/", methods=("POST",))
def add_comment():

    form = CommentForm()
    if form.validate_on_submit():
        comments = session.pop('comments', [])
        comments.append(form.comment.data)
        session['comments'] = comments
        flash("You have added a new comment")
        return redirect(url_for("index"))
    return index(form)


@auth.route('/contact/', methods=['GET', 'POST'])
def contact():
    form = ContactForm()

    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('contact.html', form=form)
    if form.validate_on_submit():
        msg = Message(form.subject.data, sender='[email protected]', recipients=[
                      '[email protected]'])
        msg.body = """ 
        From: %s <%s> 
        %s 
        """ % (form.name.data, form.email.data, form.message.data)
        mail.send(msg)

        return render_template('contact.html', success=True)

    elif request.method == 'GET':
        return render_template('contact.html', form=form)
