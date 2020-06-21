from flask import Blueprint, render_template, session, redirect, url_for, request, flash,make_response
from .model import User
from .forms import LoginForm, CategoryForm, ContactForm
from flask import g
from flask_mail import Message,Mail
from werkzeug.security import generate_password_hash,check_password_hash
from threading import Thread
from flask import current_app




auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'], endpoint='login')
def login():
    form = LoginForm()
    if request.method == 'POST':
        try:
            if form.validate_on_submit():
                return redirect(url_for('index'))
        except Exception as e:
            flash(f'用户名或密码错误{str(e)}', 'error')
            return render_template('auth/login.html', form=form)
    return render_template('auth/login.html', form=form,login='bg-info')


@auth.route('/logout',methods=['GET', 'POST'] ,endpoint='logout')
def logout():
    # remove the username from the session if it's there
    session.pop('user_id', None)
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('auth.login'))


@auth.route('/get_cookie', methods=['GET', 'POST'], endpoint='get_cookie')
def get_cookie():
    username = request.cookies.get('username')
    return username
    # use cookies.get(key) instead of cookies[key] to not get a
    # KeyError if the cookie is missing.


@auth.route('/set_cookie', methods=['GET', 'POST'], endpoint='set_cookie')
def set_cookie():
    resp = make_response(render_template(...))
    resp.set_cookie('username', 'the username')
    return resp

