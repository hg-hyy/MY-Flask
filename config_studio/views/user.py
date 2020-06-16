from flask import Blueprint,render_template
# from config_studio import db
from .forms import UserForm
from .model import User,db

user = Blueprint('user',__name__)



@user.route('/add_user',methods=['GET','POST'],endpoint='add_user')
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        user= User(username=username, email=email,password=password)
        db.session.add(user)
        db.session.commit()
        user_list = User.query.all()
        return render_template('user/show_users.html', user_list=user_list)
    return render_template('user/add_user.html', form=form)
        
@user.route('/delete_user/<username>',methods=['GET','POST'],endpoint='delete_user')
def delete_user(username):
    username = User.query.filter_by(username=username).first()
    print('hello')
    db.session.delete(username)
    db.session.commit()
    user_list = User.query.all()
    return render_template('user/show_users.html',user_list=user_list)

@user.route('/select_user/<username>',methods=['GET','POST'],endpoint='select_user')
def select_user(username):
    user = User.query.filter_by(username=username).first_or_404(description='There is no data with {}'.format(username))
    return render_template('user/select_user.html', user=user)

@user.route('/show_users',methods=['GET','POST'],endpoint='user/show_users')
def show_users():
    user_list = User.query.all()
    return render_template('user/show_users.html', user_list=user_list)

@user.route('/profile',methods=['GET','POST'])
def profile():
    return render_template('user/profile.html')

@user.route('/setting')
def setting():
    return render_template('user/setting.html')