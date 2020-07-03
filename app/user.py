from flask import Blueprint, render_template, request, flash, url_for,abort,redirect
from .forms import RegisterForm
from .model import User, db
from app.opc import login_required




admin = Blueprint('admin', __name__,url_prefix='/admin')


@admin.route('/add', methods=['GET', 'POST'], endpoint='add')
def add(admin_create=False):
    if admin_create:
        msg = 'Administrator creation is forbidden,Please contact author'
        abort(403, msg)
    form = RegisterForm()
    if request.method == 'POST':
        try:
            if form.validate_on_submit():
                return redirect(url_for('admin.admin'))
        except Exception as e:
            print(str(e))
    return render_template('user/add_user.html', form=form)


@admin.route('/delete/<username>', methods=['GET', 'POST'], endpoint='delete')
def delete_user(username):
    username = User.query.filter_by(username=username).first()
    db.session.delete(username)
    db.session.commit()
    return redirect(url_for('admin.admin'))


def get_user(username):
    user = User.query.filter_by(username=username).first_or_404(
        description='There is no data with {}'.format(username))
    return user


@admin.route('/', methods=['GET', 'POST'], endpoint='admin')
@login_required
def show_users():
    user_list = User.query.all()
    return render_template('user/show_users.html', user_list=user_list)


@admin.route('/profile', methods=['GET', 'POST'],endpoint='profile')
@login_required
def profile():
    return render_template('user/profile.html')

