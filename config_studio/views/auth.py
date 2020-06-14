from flask import Blueprint, render_template, session, redirect, url_for, request
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms import BooleanField
from wtforms.validators import DataRequired
import json
import xlrd
from pathlib import Path
from werkzeug.utils import secure_filename
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import widgets
from config_studio import db
from .model import User
from .forms import LoginForm
from flask import make_response,flash
from flask import g


auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'],endpoint='login')
def login():
    form = LoginForm()
    if request.method=='POST':
        if form.validate_on_submit():
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first_or_404(description='THE {} is not found'.format(username))
            if user.username==username and user.password ==password:
                session['username'] = request.form['username']
                flash('You were successfully logged in','sucess')
                return redirect(url_for('cs.index'))
            else:
                error_msg='登陆失败'
                return render_template('auth/login.html', error_msg=error_msg,form=form)
            error_msg= '验证失败'
            return render_template('auth/login.html',form=form,error_msg=error_msg)
    return render_template('auth/login.html',form=form)


@auth.route('/logout',endpoint='logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    # return redirect(url_for('home.index'))
    return render_template('auth/logout.html')




from flask import request

@auth.route('/get_cookie',methods=['GET', 'POST'],endpoint='get_cookie')
def get_cookie():
    username = request.cookies.get('username')
    # use cookies.get(key) instead of cookies[key] to not get a
    # KeyError if the cookie is missing.


@auth.route('/set_cookie',methods=['GET', 'POST'],endpoint='set_cookie')
def set_cookie():
    resp = make_response(render_template(...))
    resp.set_cookie('username', 'the username')
    return resp
