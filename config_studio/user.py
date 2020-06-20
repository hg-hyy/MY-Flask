from flask import Blueprint, render_template, request, flash, session, url_for,abort
from .forms import RegisterForm, LoginForm
from .model import User, db
from config_studio.config_studio import login_required
from werkzeug.security import generate_password_hash,check_password_hash



user = Blueprint('user', __name__)


@user.route('/add_user', methods=['GET', 'POST'], endpoint='add_user')
def add_user(admin_create=False):
    if admin_create:
        msg = 'Administrator creation is forbidden,Please contact author'
        abort(403, msg)
    form = RegisterForm()
    if request.method == 'POST':
        try:
            if form.validate_on_submit():
                user_list = User.query.all()
                return render_template('user/show_users.html', user_list=user_list)
        except Exception as e:
            print(str(e))
    return render_template('user/add_user.html', form=form)


@user.route('/delete_user/<username>', methods=['GET', 'POST'], endpoint='delete_user')
def delete_user(username):
    username = User.query.filter_by(username=username).first()
    print('hello')
    db.session.delete(username)
    db.session.commit()
    user_list = User.query.all()
    return render_template('user/show_users.html', user_list=user_list)


@user.route('/select_user/<username>', methods=['GET', 'POST'], endpoint='select_user')
def select_user(username):
    user = User.query.filter_by(username=username).first_or_404(
        description='There is no data with {}'.format(username))
    return render_template('user/select_user.html', user=user)


@user.route('/show_users', methods=['GET', 'POST'], endpoint='show_users')
@login_required
def show_users():
    user_list = User.query.all()
    return render_template('user/show_users.html', user_list=user_list)


@user.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    return render_template('user/profile.html')


@user.route('/setting')
def setting():
    return render_template('user/setting.html')



