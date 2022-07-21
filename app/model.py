from flask_sqlalchemy import SQLAlchemy
import datetime
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedSerializer as Serializer


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    create_time = db.Column(db.DateTime, index=True,
                            default=datetime.datetime.now())
    last_login_time = db.Column(
        db.DateTime, index=True, default=datetime.datetime.now(),onupdate=datetime.datetime.now())
    is_superuser = db.Column(db.Boolean, default=False,nullable=True)
    _password = db.Column(db.String(128), unique=True, nullable=False)
    # issue = db.relationship('Issue', backref='User', lazy=True)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, raw):
        self._password = generate_password_hash(raw)

    def check_password(self, rw_pwd):
        return check_password_hash(self._password, rw_pwd)
        # return True

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.username})

    def confirm_email(self, token, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except Exception:
            return False
        if data.get('confirm') != self.username:
            return False
        self.confirmed = True
        self.save()
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.username})

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)

        except Exception:
            return False

        try:
            user = User.objects.get(username=data.get('reset'))

        except Exception:
            return False

        user.password = new_password
        user.save()

        return True

    def get_id(self):
        try:
            return self.id
        except AttributeError:
            raise NotImplementedError(
                'No `username` attribute - override `get_id`')

    def __unicode__(self):
        return self.username

    def __str__(self):
        return self.username

    def to_json(self):
        return{
            'id':self.id,
            'username':self.username,
            'email':self.email,
            'create_time':self.create_time,
            'last_login_time':self.last_login_time,
            'is_superuser':self.is_superuser,
            '_password':self._password,
        }
class Opc(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    main_server_ip = db.Column(db.String(80), unique=True, nullable=False)
    main_server_prgid = db.Column(db.String(120), unique=True, nullable=True)
    main_server_clsid = db.Column(db.String(120), unique=True, nullable=True)
    main_server_domain = db.Column(db.String(120), unique=True, nullable=True)
    main_server_user = db.Column(db.String(120), unique=True, nullable=True)
    main_server_password = db.Column(
        db.String(120), unique=True, nullable=False)

    bak_server_ip = db.Column(db.String(80), unique=True, nullable=False)
    bak_server_prgid = db.Column(db.String(120), unique=True, nullable=True)
    bak_server_clsid = db.Column(db.String(120), unique=True, nullable=True)
    bak_server_domian = db.Column(db.String(120), unique=True, nullable=True)
    bak_server_user = db.Column(db.String(120), unique=True, nullable=True)
    bak_server_password = db.Column(
        db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return '<Opc %r>' % self.main_server_progid

    def __str__(self):
        return self.main_server_progid


class Modbus(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    dev_id = db.Column(db.String(80), unique=True, nullable=False)
    Coll_Type = db.Column(db.String(120), unique=True, nullable=True)

    host = db.Column(db.String(120), unique=True, nullable=True)
    port = db.Column(db.String(120), unique=True, nullable=True)

    serial = db.Column(db.String(120), unique=True, nullable=True)
    baud = db.Column(db.String(120), unique=True, nullable=False)
    data_bit = db.Column(db.String(80), unique=True, nullable=False)
    stop_bit = db.Column(db.String(120), unique=True, nullable=True)
    parity = db.Column(db.String(120), unique=True, nullable=True)

    def __repr__(self):
        return '<Modbus %r>' % self.dev_id

    def __str__(self):
        return self.dev_id


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    created = db.Column(db.DateTime, index=True, default=datetime.datetime.now(
    ), onupdate=datetime.datetime.now())
    issue = db.relationship('Issue', backref=db.backref('Category', lazy=True),overlaps="Category,issue")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='Category', lazy=True)

    def __str__(self):
        return self.name
    
    def to_json(self):
        return{
            'id':self.id,
            'name':self.name,
            'created':self.created,
            'issue':[issue.to_json() for issue in self.issue ],
            'user_id':self.user_id,
            'user':self.user.username,
        }



class Issue(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, index=True, default=datetime.datetime.now(
    ), onupdate=datetime.datetime.now())
    title = db.Column(db.String(120), unique=True, nullable=True)
    body = db.Column(db.String(120), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey(
        'category.id'), nullable=False)
    category = db.relationship(
        'Category', backref=db.backref('Issue', lazy=True),overlaps="Category,issue")
    user = db.relationship('User', backref='Issue', lazy=True)

    def __repr__(self):
        return '<Issue %r>' % self.title

    def __str__(self):
        return self.title

    def __unicode__(self):
        return self.body[:64]
    meta = {
        'ordering': ['-created']
    }
    def to_json(self):
        return{
            'id':self.id,
            'created':self.created,
            'title':self.title,
            'body':self.body,
            'user_id':self.user_id,
            'category_id':self.category_id,
            'category':self.category.name,
            'user':self.user.username,
        }

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, index=True, default=datetime.datetime.now(
    ), onupdate=datetime.datetime.now())
    name = db.Column(db.String(120), unique=False, nullable=True)
    email = db.Column(db.String(120), unique=False, nullable=False)
    subject = db.Column(db.String(120), unique=False, nullable=True)
    message = db.Column(db.String(120), unique=False, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    User = db.relationship('User', backref='Contact', lazy=True)

    def __repr__(self):
        return '<Issue %r>' % self.title

    def __str__(self):
        return self.title
